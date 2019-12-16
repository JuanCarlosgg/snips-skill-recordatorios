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
    import json
    from datetime import datetime
    import paho.mqtt.client as mqtt
    import paho.mqtt.publish as mqtt_publish
    
    if len(intentMessage.slots.Hora or intentMessage.slots.Frecuencia or intentMessage.slots.Medicina) > 0:
            try:
              valueMedicina = intentMessage.slots.Medicina.first().value 
            except:
               valueMedicina = ""
    
            try:
              valueHora = intentMessage.slots.Hora.first().value
              dates = valueHora[0:19]
              date = datetime.strptime(dates, "%Y-%m-%d %H:%M:%S")
              hour = date.strftime("%H")
              minute = date.strftime("%M")
              weekday = date.weekday() +1
            except:
              hour = "10"
              minute= "0"
              weekday = 1
    
            try:
              valueFreq = int(intentMessage.slots.Frecuencia.first().value)
            except:
              valueFreq = weekday
    
    
            concept = 0
            #Paracetamol
            if (valueMedicina == "Paracetamol"):
              concept = 1
            #Aspirina
            elif (valueMedicina == "Aspirina"):
              concept = 2
            #Ibuprofeno
            elif (valueMedicina == "Ibuprofeno"):
              concept = 3
            
            print(concept, valueFreq, hour, minute )
            if (valueFreq <= 7): 
              client = mqtt.Client()
              client.connect('localhost', 1883)
              client.publish("/dsh/damaso/reminders/management",json.dumps({
                "action": "ADD",
                "hour": int(hour),
                "minute": int(minute),
                "weekday": valueFreq,
                "concept": concept
                }))
            else:
              if (valueFreq == 12):
                list_msg = []
                for i in range(0,7):
                  list_msg.append({
                    "topic": "/dsh/damaso/reminders/management",
                    "payload": json.dumps({"action": "ADD",
                    "hour": int(hour),
                    "minute": int(minute),
                    "weekday": i+1,
                    "concept": concept           
                    })})
    
                  list_msg.append({
                    "topic": "/dsh/damaso/reminders/management",
                    "payload": json.dumps({
                    "action": "ADD",
                    "hour": int(hour)+12,
                    "minute": int(minute),
                    "weekday": i+1,
                    "concept": concept          
                    })})
                mqtt_publish.multiple(list_msg, hostname="localhost", port=1883)
              elif (valueFreq == 24):
                list_msg = []
                for i in range(0,7):
                  list_msg.append({
                    "topic": "/dsh/damaso/reminders/management",
                    "payload": json.dumps({"action": "ADD",
                    "hour": int(hour),
                    "minute": int(minute),
                    "weekday": i+1,
                    "concept": concept         
                    })})
                mqtt_publish.multiple(list_msg, hostname="localhost", port=1883)
    
    
            #print(value)
            result_sentence = "De acuerdo."  
    else:
        result_sentence = "No te he entendido"        
    hermes.publish_end_session(intentMessage.session_id, result_sentence)
    


if __name__ == "__main__":
    mqtt_opts = MqttOptions()
    with Hermes(mqtt_options=mqtt_opts) as h:
        h.subscribe_intent("juancarlos:Medicina", subscribe_intent_callback) \
         .start()
