##############################
# Responses
##############################


def conversation(title, body, session_attributes):
    speechlet = {}
    speechlet['outputSpeech'] = build_PlainSpeech(body)
    speechlet['card'] = build_SimpleCard_image(body)
    speechlet['shouldEndSession'] = False
    return build_response(speechlet, session_attributes=session_attributes)


def simple_statement(body):
    speechlet = {}
    speechlet['outputSpeech'] = build_PlainSpeech(body)
    speechlet['card'] = build_SimpleCard(body)
    speechlet['shouldEndSession'] = True
    return build_response(speechlet)


def statement(body):
    speechlet = {}
    speechlet['outputSpeech'] = build_PlainSpeech(body)
    speechlet['card'] = build_SimpleCard_image(body)
    speechlet['shouldEndSession'] = True
    return build_response(speechlet)


def continue_dialog():
    message = {}
    message['shouldEndSession'] = False
    message['card'] = build_SimpleCard_image(None)
    message['directives'] = [{'type': 'Dialog.Delegate'}]
    return build_response(message)


def build_PlainSpeech(body):
    speech = {}
    speech['type'] = 'PlainText'
    speech['text'] = body
    return speech


##############################
# Card Builders
##############################

def build_response(message, session_attributes={}):
    response = {}
    response['version'] = '1.0'
    response['sessionAttributes'] = session_attributes
    response['response'] = message
    return response


def build_SimpleCard(body):
    card = {}
    card['type'] = 'Simple'
    card['title'] = 'Tello'
    card['content'] = body
    return card


def build_SimpleCard_image(body):
    card = {}
    card['type'] = 'Standard'
    card['title'] = 'Tello'
    card['text'] = body
    card['image'] = {}
    card['image'][
        'smallImageUrl'] = 'https://product3.djicdn.com/uploads/photos/33900/large_851441d0-f0a6-4fbc-a94a-a8fddcac149f.jpg'
    card['image'][
        'largeImageUrl'] = 'https://product3.djicdn.com/uploads/photos/33900/large_851441d0-f0a6-4fbc-a94a-a8fddcac149f.jpg'

    return card
