#include "Config.h"
#include "WIFI.h"
#include "Server.h"

#include <PubSubClient.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.hpp>
#include <ArduinoJson.h>
#include <FastBot.h>

#define button D0
#define led_cools_down D1
#define led_hot D2

bool cold = true; // Проверяться будет остывание
int temperature = 20;

float last = 0;
bool find_max = false;
bool cools_down = false;
bool start = false;

int temperature_rise = 0;
int temperature_drop = 0;

int cools_down_number = 0;
int wait_time = 0;

bool connect = false;
String state_topic = (String)ESP.getChipId();
String topic = (String)ESP.getChipId() + "/command";

unsigned long last_millis = 0;

// Mqtt start
PubSubClient mqtt_client(wifiClient);

void callBack(char *topic, byte *payload, unsigned int length){
  if ((char)payload[0] == 'h' || (char)payload[0] == 'c'){
    Serial.print("[MQTT] Запрос на запуск, проверка что температура ");
    if ((char)payload[0] == 'h'){
      Serial.print("больше чем ");
      cold = false;
    }else if ((char)payload[0] == 'c'){
      Serial.print("меньше чем ");
      cold = true;
    }
    Serial.println(temperature);
    start_work();
  }else if (length <= 3){
    Serial.print("[MQTT] Запрос на смену температуры. Новая температура равна ");
    temperature = 0;
    int min = 1;
    int n = 0;
    if ((char)payload[0] == '-'){
      min *= -1;
      n = 1;
    }
    for (int i = n; i < length; i++){
      temperature += ((char)payload[i] - '0') * pow(10, length - i - 1);
    }
    temperature *= min;
    Serial.println(temperature);
  } else {
    Serial.println("[MQTT] Отправлена неизвестная команда!");
  }
}

bool init_MQTT() {
  int i = 0;
  mqtt_client.setServer(mqtt_broker, mqtt_port); // connect to broker
  mqtt_client.setCallback(callBack);
  while (!mqtt_client.connected()){
    String Client_id = (String)ESP.getChipId() + "-client_id";
    if (mqtt_client.connect(Client_id.c_str())) {
      Serial.println("[MQTT] MQTT client connected with id " + Client_id);
    } else {
      i += 1;
      Serial.println("Failed to connect MQTT with " + Client_id);
      if (i == 20) return false;
      delay(1000);
    }
  }
  return true;
}
// Mqtt end

void start_work(){
  start = true;
  find_max = true;
  cools_down = false;
  if (cold){
    digitalWrite(led_hot, HIGH);
    digitalWrite(led_cools_down, LOW);
  } else {
    digitalWrite(led_hot, LOW);
    digitalWrite(led_cools_down, HIGH);
  }
  int val = analogRead(A0);
  last = val;
  cools_down_number = 0;
  Serial.println("[SENSOR] Начало получения данных");
}

void end_work(){
  start = false;
  find_max = false;
  cools_down = false;
  digitalWrite(led_hot, LOW);
  digitalWrite(led_cools_down, LOW);
  wait_time = 0;
  temperature_drop = 0;
  temperature_rise = 0;
  Serial.println("[SENSOR] Конец получения данных");
}

void get_data(int val){
  Serial.print("[SENSOR] Получены данные о температуре за 4-х секундный период: ");
  Serial.println(val);
  if (abs(last - val) <= 2){
    String text_1 = (String)ESP.getChipId() + " Данные о температуре за последние 4 секунды: "+ (String)val;
    mqtt_client.publish(state_topic.c_str(), text_1.c_str());

    if (val > temperature_rise) temperature_rise = val;
    if (val < temperature_drop) temperature_drop = val;

    if (cools_down && ((cold && temperature_drop + 2 < val) || (cold == false && temperature_rise - 2 < val))){
      cools_down = false;
      find_max = true;
      Serial.print("[SENSOR] Датчик начал ");
      if (cold){
        digitalWrite(led_hot, HIGH);
        digitalWrite(led_cools_down, LOW);
        temperature_rise = val;
        temperature_drop = 0;
        Serial.println("нагреваться");
        String text = (String)ESP.getChipId() + " Датчик начал нагреваться.";
        mqtt_client.publish(state_topic.c_str(), text.c_str());
      } else {
        digitalWrite(led_hot, LOW);
        digitalWrite(led_cools_down, HIGH);
        temperature_rise = 0;
        temperature_drop = val;
        Serial.println("охлаждаться");
        String text = (String)ESP.getChipId() + " Датчик начал охлаждаться.";
        mqtt_client.publish(state_topic.c_str(), text.c_str());
      }
    }
  }
}

void work_mod(){
  if (start && digitalRead(button)){
    Serial.println("[ESP] Кнопка была нажата");
    end_work();
    String text1 = (String)ESP.getChipId() + " Работа платформы была остановлена нажатием на кнопку.";
    String text2 = (String)ESP.getChipId() + " stop";
    mqtt_client.publish(state_topic.c_str(), text1.c_str());
    mqtt_client.publish(state_topic.c_str(), text2.c_str());
  }

  if (start) {
    int val = analogRead(A0);
    if (last_millis * 4000 != millis() && millis() % 4000 == 0){
      last_millis = millis() / 4000;
      get_data(val);
    }

    if (abs(last - val) <= 2){
      if (find_max && ((cold && temperature_rise - val > 3) || (cold == false && val - temperature_drop > 3))) cools_down_number += 1;
      if ((cold && temperature_rise - val < 3) || (cold == false && val - temperature_drop > 3)) cools_down_number = 0;
    }

    if (find_max && cools_down_number > 20){
      find_max = false;
      cools_down = true;
      cools_down_number = 0;
      if (cold){
        digitalWrite(led_hot, LOW);
        digitalWrite(led_cools_down, HIGH);
        temperature_drop = val;
        Serial.println("[SENSOR] Датчик начал охлаждаться");
        String text = (String)ESP.getChipId() + " Датчик начал охлаждаться.";
        mqtt_client.publish(state_topic.c_str(), text.c_str());
      } else {
        digitalWrite(led_hot, HIGH);
        digitalWrite(led_cools_down, LOW);
        temperature_rise = val;
        Serial.println("[SENSOR] Датчик начал нагреваться");
        String text = (String)ESP.getChipId() + " Датчик начал нагреваться.";
        mqtt_client.publish(state_topic.c_str(), text.c_str());
      }
    } else if (cools_down && ((cold && temperature_drop <= temperature) || (cold == false && temperature_rise >= temperature))){
      end_work();
      String text_2 = (String)ESP.getChipId() + " stop";
      String text_1 = (String)ESP.getChipId();
      if (cold) text_1 += " Подставка остыла до определенной температуры.";
      else text_1 += " Подставка нагрелась до определенной температуры.";
      mqtt_client.publish(state_topic.c_str(), text_1.c_str());
      mqtt_client.publish(state_topic.c_str(), text_2.c_str());
    }

    if (abs(last - val) <= 2) last = val;
  }
}

void setup() {
  Serial.begin(4800);
  Serial.println();
  Serial.println("[ESP] Запуск работы...");
  pinMode(led_hot, OUTPUT);
  pinMode(led_cools_down, OUTPUT);
}

void loop() {
  if (CLI_SSID != (char*)"") {
    connect = false;
    bool is_wifi_no = init_WIFI(false);
    if (is_wifi_no) {
      if (init_MQTT()) {
        Serial.print("[ESP] Подставка была подключена к ");
        Serial.println(CLI_SSID);
        Serial.println("[MQTT] See me at " + topic);
        digitalWrite(led_hot, LOW);
        digitalWrite(led_cools_down, LOW);
      }
    }
    CLI_SSID = "";
    CLI_PASS = "";
  }

  if (wifiMulti.run() != WL_CONNECTED){
    if (!connect){
      Serial.println("[ESP] Точка доступа создана");
      digitalWrite(led_cools_down, LOW);
      bool is_wifi_no = init_WIFI(true);
      if (is_wifi_no) server_init();
      connect = true;
    } else server.handleClient();
    digitalWrite(led_hot, millis() % 1000 < 500);
  } else {
    if (start) work_mod();
    else{
      mqtt_client.subscribe(topic.c_str());
      mqtt_client.loop();
    }
  }
}