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
    import paho.mqtt.subscribe as subscribe
    import paho.mqtt.publish as publish
    import paho.mqtt.client as mqtt
    from datetime import datetime, timedelta       
    
    
    def hours(millis):
      seconds=(millis/1000)%60
      seconds = int(seconds)
      minutes=(millis/(1000*60))%60
      minutes = int(minutes)
      hours=(millis/(1000*60*60))%24
      hours=int(hours)
      return hours, minutes, seconds
    
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        client.subscribe("/dsh/damaso/reminders/IDresponses")
    
    sentence = " "
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    tipo = ["Medicina", "Paracetamol",  "Aspirina", "Ibuprofeno", " ", " ", " ", "Médico", " ", "TV"]  
    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        #print(msg.topic+" "+str(msg.payload))
        try:
          print("Punto 1")
          recordatorios = json.loads(msg.payload)
          print(recordatorios)
          recordatorios = recordatorios["recordatorios"]
          date1 = datetime.now()
          #inicio_semana = date1 - timedelta(days=date1.weekday())  
          if len(recordatorios) > 0:
    
            print("Punto 2")
            m = list(map( lambda x: (tipo[x["sonido"]]   , hours(x["tiempo"]) , x["dia"] ,x["id"] ), json.loads(msg.payload)["recordatorios"]))
            
            print("Punto 3")
            m = list(filter(lambda x: x[2] > date1.weekday(), m))
    
            print("Punto 4")
            m2 = [ "El {} a las {} y {} recordatorio de {} ".format( dias[x[2]-1], x[1][0], x[1][1], x[0]  ) for (idx,x) in enumerate(m)]  
            sentence = " . ".join(m2)
            client.loop_stop()
            client.disconnect()
            if len(m2) <= 4:
                
              print("Punto 5.a")
              return hermes.publish_continue_session(intentMessage.session_id,
                        sentence, ['juancarlos:SeleccionarRecordatorio'],
                        custom_data=json.dumps(list(map(lambda x: x[3], m))))
            else:
                
              print("Punto 5.b")
              return hermes.publish_continue_session(intentMessage.session_id,
                        "Hay un total de {} recordatorios. ¿Cuál quieres borrar?".format(len(m2)), ['juancarlos:SeleccionarRecordatorio'],custom_data=json.dumps(list(map(lambda x: x[3], m))))
          else:
            client.loop_stop()
            client.disconnect()
            return hermes.publish_end_session(intentMessage.session_id, "No tienes ningún recordatorio programado") 
        except:
          client.loop_stop()
          client.disconnect()
          import traceback
          traceback.print_exc()  
    
         
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect("localhost", 1883, 60)
    
    client.loop(0.2)
    client.publish("/dsh/damaso/reminders/requests", "b")
    client.loop_forever()
    


if __name__ == "__main__":
    mqtt_opts = MqttOptions()
    with Hermes(mqtt_options=mqtt_opts) as h:
        h.subscribe_intent("juancarlos:Eliminar", subscribe_intent_callback) \
         .start()
