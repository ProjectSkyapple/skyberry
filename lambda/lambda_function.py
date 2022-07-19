# -*- coding: utf-8 -*-

import logging
import ask_sdk_core.utils as ask_utils
import os

api_key = "keyCZiMOUisHeZZrd"
import json

from pyairtable import Table

table = Table(api_key, "appRGAYGdR82SVVF2", "All Events")
to_do_table = Table(api_key, "appRGAYGdR82SVVF2", "All To-dos")

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


record_count = 0


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        global record_count
        record_count = 0

        speak_output = 'Welcome to Earthorange. Earthorange helps you find and participate in volunteer opportunities in the Rio Grande Valley. \
                        Let\'s start! What are you interested in? You can say "Arts," "Business," "Education," "Environment," "Health," or "STEM."'
        reprompt_text = "I'm interested in STEM. What's one thing you're interested in?"

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(reprompt_text)
            .response
        )


class CaptureInterestIntentHandler(AbstractRequestHandler):
    """Handler for capturing a user's interest."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CaptureInterestIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes

        slots = handler_input.request_envelope.request.intent.slots
        interest = slots["interest"].value

        records = table.all(view="Grid view")

        global record_count
        record_count += 1

        entry = records[record_count - 1]  # Returns a dict
        entry_fields = entry["fields"]
        event_name = entry_fields["Event Name"]
        host_name = entry_fields["Host Name"]
        start_date = entry_fields["Start Date Formatted"]
        start_time = entry_fields["Start Time"]
        end_date = entry_fields["End Date Formatted"]
        end_time = entry_fields["End Time"]

        if start_date == end_date:
            speak_output = 'Great! Let me find some volunteer opportunities related to {interest}. \
                            I found one. It\'s called "{event_name}." {host_name} is hosting the event. The event starts on {start_date} at \
                            {start_time} and ends at {end_time}. Want to learn more about this event?'.format(
                interest=interest,
                event_name=event_name,
                host_name=host_name,
                start_date=start_date,
                start_time=start_time,
                end_time=end_time,
            )
        else:
            speak_output = 'Great! Let me find some volunteer opportunities related to {interest}. \
                            I found one. It\'s called "{event_name}." {host_name} is hosting the event. The event starts on {start_date} at \
                            {start_time} and ends on {end_date} at {end_time}. Want to learn more about this event?'.format(
                interest=interest,
                event_name=event_name,
                host_name=host_name,
                start_date=start_date,
                start_time=start_time,
                end_date=end_date,
                end_time=end_time,
            )

        reprompt_text = "Want to learn more about this event?"

        session_attr["intent_ended"] = "CaptureInterestIntent"

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(reprompt_text)
            .response
        )


class YesCaptureInterestIntentHandler(AbstractRequestHandler):
    """Handler for YesCaptureInterestIntent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        session_attr = handler_input.attributes_manager.session_attributes

        return (
            ask_utils.is_intent_name("AMAZON.YesIntent")(handler_input)
            and session_attr["intent_ended"] == "CaptureInterestIntent"
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes

        records = table.all(view="Grid view")
        entry = records[record_count - 1]
        entry_fields = entry["fields"]
        host_name = entry_fields["Host Name"]
        try:
            is_virtual = entry_fields["Virtual?"]
        except KeyError:
            is_virtual = False
        location = entry_fields["Location"]
        summary = entry_fields["Summary"]

        if is_virtual:
            speak_output = "This event occurs online. Here's what {host_name} has to say: {summary} \
                            To learn more about the event, add this event to your to-do list. \
                            Do you want to add this event to your Earthorange to-do list?".format(
                host_name=host_name, summary=summary
            )
        else:
            speak_output = "This event occurs at {location}. Here's what {host_name} has to say: {summary} \
                            Do you want to add this event to your Earthorange to-do list?".format(
                location=location, host_name=host_name, summary=summary
            )

        reprompt_text = "Do you want to add this event to your Earthorange to-do list?"

        session_attr["intent_ended"] = "YesIntent-CaptureInterest"

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(reprompt_text)
            .response
        )


class AddToDoIntentHandler(AbstractRequestHandler):
    """Handler for AddToDoIntent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        session_attr = handler_input.attributes_manager.session_attributes

        return ask_utils.is_intent_name("AMAZON.YesIntent")(handler_input) and (
            session_attr["intent_ended"] == "YesIntent-CaptureInterest"
            or session_attr["intent_ended"] == "NoIntent-CaptureInterest"
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes

        global record_count

        records = table.all(view="Grid view")
        entry = records[record_count - 1]
        entry_id = entry["id"]
        entry_fields = entry["fields"]
        event_name = entry_fields["Event Name"]

        selected_event_record = table.get(entry_id)
        ser_fields = selected_event_record["fields"]
        ser_followers = ser_fields["Followers"]

        ser_followers.append("recxeZwAxjfy2kfAn")
        table.update(entry_id, {"Followers": ser_followers})

        speak_output = 'OK, I\'ve added "{event_name}" to your to-do list in your Earthorange app.'.format(
            event_name=event_name
        )

        record_count = 0

        session_attr["intent_ended"] = "Finished"

        return handler_input.response_builder.speak(speak_output).response


class NoCaptureInterestIntentHandler(AbstractRequestHandler):
    """Handler for NoCaptureInterestIntent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        session_attr = handler_input.attributes_manager.session_attributes

        return (
            ask_utils.is_intent_name("AMAZON.NoIntent")(handler_input)
            and session_attr["intent_ended"] == "CaptureInterestIntent"
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes

        speak_output = "Do you want to add this event to your Earthorange to-do list?"
        reprompt_text = "Do you want to add this event to your Earthorange to-do list?"

        session_attr["intent_ended"] = "NoIntent-CaptureInterest"

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(reprompt_text)
            .response
        )


class RetryHandler(AbstractRequestHandler):
    """Handler for RetryHandler."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        session_attr = handler_input.attributes_manager.session_attributes

        return ask_utils.is_intent_name("AMAZON.NoIntent")(handler_input) and (
            (
                session_attr["intent_ended"] == "NoIntent-CaptureInterest"
                or session_attr["intent_ended"] == "YesIntent-CaptureInterest"
            )
            and record_count <= 3
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes

        global record_count
        record_count += 1

        records = table.all(view="Grid view")
        entry = records[record_count - 1]
        entry_fields = entry["fields"]
        event_name = entry_fields["Event Name"]
        host_name = entry_fields["Host Name"]
        start_date = entry_fields["Start Date Formatted"]
        start_time = entry_fields["Start Time"]
        end_date = entry_fields["End Date Formatted"]
        end_time = entry_fields["End Time"]

        if start_date == end_date:
            speak_output = 'OK, I have another event you might be interested in. It\'s called "{event_name}." {host_name} is hosting the event. The event starts on {start_date} at \
                            {start_time} and ends at {end_time}. Want to learn more about this event?'.format(
                event_name=event_name,
                host_name=host_name,
                start_date=start_date,
                start_time=start_time,
                end_time=end_time,
            )
        else:
            speak_output = 'OK, I have another event you might be interested in. It\'s called "{event_name}." {host_name} is hosting the event. The event starts on {start_date} at \
                            {start_time} and ends on {end_date} at {end_time}. Want to learn more about this event?'.format(
                event_name=event_name,
                host_name=host_name,
                start_date=start_date,
                start_time=start_time,
                end_date=end_date,
                end_time=end_time,
            )

        reprompt_text = "Want to learn more about this event?"

        session_attr["intent_ended"] = "CaptureInterestIntent"

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(reprompt_text)
            .response
        )


class NoInterestHandler(AbstractRequestHandler):
    """Handler for NoInterestHandler."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (
            ask_utils.is_intent_name("AMAZON.NoIntent")(handler_input)
            and record_count > 3
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes

        speak_output = (
            "OK, you can view more events available for you in your Earthorange app."
        )

        global record_count
        record_count = 0

        session_attr["intent_ended"] = "Finished"

        return handler_input.response_builder.speak(speak_output).response


class CallToDoListIntentHandler(AbstractRequestHandler):
    """Handler for CallToDoListIntentHandler."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CallToDoListIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes

        try:
            to_do_records = to_do_table.all(view="Grid view")
            user_info = to_do_records[2]
            user_fields = user_info["fields"]
            user_to_dos = user_fields["To-dos"]

            event_name_list = []
            start_date_list = []
            start_time_list = []
            event_status_list = []

            event_records = table.all(view="Grid view")

            for i in range(0, len(user_to_dos)):
                selected_event_record = user_to_dos[i]
                entry = table.get(selected_event_record)
                entry_fields = entry["fields"]

                event_name = entry_fields["Event Name"]
                event_name_list.append(event_name)

                start_date = entry_fields["Start Date Formatted"]
                start_date_list.append(start_date)

                start_time = entry_fields["Start Time"]
                start_time_list.append(start_time)

                try:
                    if entry_fields["Scheduled?"]:
                        event_status = "is currently scheduled"
                except:
                    try:
                        if entry_fields["Changed?"]:
                            event_status = "has changed"
                    except:
                        if entry_fields["Canceled?"]:
                            event_status = "has been canceled"

                event_status_list.append(event_status)

            speak_output = "Here's what's on your Earthorange to-do list. "

            for i in range(0, len(user_to_dos)):
                speak_output += 'The event "{event_name_list}" scheduled for {start_date_list} at {start_time_list} {event_status_list}. '.format(
                    start_date_list=start_date_list[i],
                    start_time_list=start_time_list[i],
                    event_name_list=event_name_list[i],
                    event_status_list=event_status_list[i],
                )
        except KeyError:
            speak_output = "There are no events on your Earthorange to-do list. It would be awesome if you added one."

        session_attr["intent_ended"] = "Finished"

        return handler_input.response_builder.speak(speak_output).response


deleting_to_do = ""


class InitialRemoveToDoIntentHandler(AbstractRequestHandler):
    """Handler for InitialRemoveToDoIntent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("InitialRemoveToDoIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes

        records = to_do_table.all(view="Grid view")
        user_info = records[2]
        user_fields = user_info["fields"]

        try:
            user_to_dos = user_fields["To-dos"]
            selected_to_do = user_to_dos[0]
            global deleting_to_do
            deleting_to_do = selected_to_do
            entry = table.get(selected_to_do)
            entry_fields = entry["fields"]
            event_name = entry_fields["Event Name"]
            start_date = entry_fields["Start Date Formatted"]
            start_time = entry_fields["Start Time"]

            speak_output = 'Do you want to remove from your Earthorange to-do list "{event_name}" which starts on {start_date} at {start_time}?'.format(
                event_name=event_name, start_date=start_date, start_time=start_time
            )
            reprompt_text = speak_output

            session_attr["intent_ended"] = "InitialRemoveToDoIntent"
        except KeyError:
            speak_output = "There's nothing on your Earthorange to-do list."

            session_attr["intent_ended"] = "Finished"

        try:
            return (
                handler_input.response_builder.speak(speak_output)
                .ask(reprompt_text)
                .response
            )
        except NameError:
            return handler_input.response_builder.speak(speak_output).response


class YesRemoveToDoIntentHandler(AbstractRequestHandler):
    """Handler for YesRemoveToDoIntent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        session_attr = handler_input.attributes_manager.session_attributes

        return ask_utils.is_intent_name("AMAZON.YesIntent")(handler_input) and (
            session_attr["intent_ended"] == "InitialRemoveToDoIntent"
            or session_attr["intent_ended"] == "IterativeRemoveToDoIntent"
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes

        records = to_do_table.all(view="Grid view")
        user_info = records[2]
        user_fields = user_info["fields"]
        user_to_dos = user_fields["To-dos"]

        user_to_dos.remove(deleting_to_do)
        to_do_table.update("recxeZwAxjfy2kfAn", {"To-dos": user_to_dos})

        speak_output = "OK, I've removed that event from your Earthorange to-do list."

        session_attr["intent_ended"] = "Finished"

        return handler_input.response_builder.speak(speak_output).response


ItRTDI_counter = 0


class IterativeRemoveToDoIntentHandler(AbstractRequestHandler):
    """Handler for IterativeRemoveToDoIntent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        session_attr = handler_input.attributes_manager.session_attributes

        return ask_utils.is_intent_name("AMAZON.NoIntent")(handler_input) and (
            session_attr["intent_ended"] == "InitialRemoveToDoIntent"
            or session_attr["intent_ended"] == "IterativeRemoveToDoIntent"
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes

        records = to_do_table.all(view="Grid view")
        user_info = records[2]
        user_fields = user_info["fields"]
        user_to_dos = user_fields["To-dos"]

        global ItRTDI_counter
        ItRTDI_counter += 1

        try:
            selected_to_do = user_to_dos[ItRTDI_counter]
            global deleting_to_do
            deleting_to_do = selected_to_do
            entry = table.get(selected_to_do)
            entry_fields = entry["fields"]
            event_name = entry_fields["Event Name"]
            start_date = entry_fields["Start Date Formatted"]
            start_time = entry_fields["Start Time"]

            speak_output = 'How about "{event_name}" which starts on {start_date} at {start_time}?'.format(
                event_name=event_name, start_date=start_date, start_time=start_time
            )
            reprompt_text = speak_output

            session_attr["intent_ended"] = "IterativeRemoveToDoIntent"
        except IndexError:
            ItRTDI_counter = 0

            speak_output = (
                "OK, I didn't remove anything from your Earthorange to-do list."
            )

            session_attr["intent_ended"] = "Finished"

        try:
            return (
                handler_input.response_builder.speak(speak_output)
                .ask(reprompt_text)
                .response
            )
        except NameError:
            return handler_input.response_builder.speak(speak_output).response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(speak_output)
            .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.CancelIntent")(
            handler_input
        ) or ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return handler_input.response_builder.speak(speak_output).response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder.speak(speak_output)
            # .ask("add a reprompt if you want to keep the session open for the user to respond")
            .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(speak_output)
            .response
        )


# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CaptureInterestIntentHandler())
sb.add_request_handler(YesCaptureInterestIntentHandler())
sb.add_request_handler(AddToDoIntentHandler())
sb.add_request_handler(NoCaptureInterestIntentHandler())
sb.add_request_handler(RetryHandler())
sb.add_request_handler(NoInterestHandler())
sb.add_request_handler(CallToDoListIntentHandler())
sb.add_request_handler(InitialRemoveToDoIntentHandler())
sb.add_request_handler(YesRemoveToDoIntentHandler())
sb.add_request_handler(IterativeRemoveToDoIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(
    IntentReflectorHandler()
)  # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
