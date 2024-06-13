#include <Arduino.h>

String AP_NAME = "TemperarureStand";
String AP_PASSWORD = (String)ESP.getChipId();

char* CLI_SSID = "";
char* CLI_PASS = ""; 

int WEB_SERVER_PORT = 80;

const int mqtt_port = 1883;
char* mqtt_broker = "broker.emqx.io";