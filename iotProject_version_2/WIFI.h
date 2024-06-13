#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ESP8266WiFiMulti.h>

ESP8266WiFiMulti wifiMulti;
WiFiClient wifiClient;

String ip = "IP not set";

String id() {
  int mac_len = WL_MAC_ADDR_LENGTH;
  uint8_t mac[mac_len];
  WiFi.softAPmacAddress(mac);
  String mac_id = String(mac[mac_len-2], HEX) +
                  String(mac[mac_len-1], HEX);
  return mac_id;
}

bool start_AP_mode() {
  String ssid_id = AP_NAME + id();
  IPAddress ap_IP(192, 168, 4, 1);
  WiFi.disconnect();
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(ap_IP, ap_IP, IPAddress(255, 255, 255, 0));
  WiFi.softAP(ssid_id.c_str(), AP_PASSWORD.c_str());
  Serial.println("WiFi started in AP mode " + ssid_id);
  Serial.println("WiFi password " + AP_PASSWORD);
  return true;
}

bool start_client_mode() {
  int i = 0;
  wifiMulti.addAP(CLI_SSID, CLI_PASS);
  while(wifiMulti.run() != WL_CONNECTED) {
    Serial.println(CLI_SSID);
    Serial.println(CLI_PASS);
    i += 1;
    if (i = 4) return false;
    delay(10);
  }
  return true;
}

bool init_WIFI(bool AP_mode){
  WiFi.softAPdisconnect(true);
  if (AP_mode){
    start_AP_mode();
    ip = WiFi.softAPIP().toString();
    Serial.print("IP address: ");
    Serial.print(ip);
    Serial.println("");
  }
  else {
    start_client_mode();
    ip = WiFi.localIP().toString();
  }
  
  return true;
}