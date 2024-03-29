#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
from hermes_python.hermes import Hermes
from hermes_python.ffi.utils import MqttOptions
from hermes_python.ontology import *
import io

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

class SnipsConfigParser(configparser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, configparser.Error) as e:
        return dict()

def subscribe_intent_callback(hermes, intentMessage):
    conf = read_configuration_file(CONFIG_INI)
    action_wrapper(hermes, intentMessage, conf)


def action_wrapper(hermes, intentMessage, conf):
    """ Write the body of the function that will be executed once the intent is recognized. 
    In your scope, you have the following objects : 
    - intentMessage : an object that represents the recognized intent
    - hermes : an object with methods to communicate with the MQTT bus following the hermes protocol. 
    - conf : a dictionary that holds the skills parameters you defined. 
      To access global parameters use conf['global']['parameterName']. For end-user parameters use conf['secret']['parameterName'] 
     
    Refer to the documentation for further details. 
    """ 
    import paho.mqtt.publish as publish
    import json
    
    if len(intentMessage.slots.numero) > 0:
      num = int(intentMessage.slots.numero.first().value)
      l = json.loads(intentMessage.custom_data)
      print(l)
      publish.single("/dsh/damaso/reminders/management", json.dumps({"action": "DEL", "id": l[num-1] }), hostname="localhost")
      #publicar en     LISTEN_CHANNEL = "/dsh/damaso/reminders/management" un objeto con el atributo 'id'
      result_sentence = "De acuerdo, borrando el recordatorio número" + str(num)
      hermes.publish_end_session(intentMessage.session_id, result_sentence)
    else:
      hermes.publish_end_session(intentMessage.session_id, "No te he entendido")
    


if __name__ == "__main__":
    mqtt_opts = MqttOptions()
    with Hermes(mqtt_options=mqtt_opts) as h:
        h.subscribe_intent("juancarlos:SeleccionarRecordatorio", subscribe_intent_callback) \
         .start()
