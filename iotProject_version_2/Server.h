#include <ESP8266WebServer.h>

ESP8266WebServer server(80);

void handle_root(){
  String page_code = "<form action=\"/wifi\" method=\"POST\">";
  page_code += "<label>Enter the name of your network to connect the stand:</label><br>";
  page_code += "<label>login:</label><input type=\"text\" name=\"ssid\"><br><label>password:</label><input type=\"text\" name=\"pass\"><br><button type=\"submit\">send</button></form>";
  server.send(200, "text/html", page_code);
}

void handle_wifi(){
  unsigned char* buf = new unsigned char[100];
  String str = server.arg("ssid").c_str();
  str.getBytes(buf, 100, 0);
  CLI_SSID = (char*)buf; // turn phone AP 5 GHz -> 2.4 GHz

  unsigned char* buf2 = new unsigned char[100];
  String str2 = server.arg("pass").c_str();
  str2.getBytes(buf2, 100, 0);
  CLI_PASS = (char*)buf2;

  server.sendHeader("Location", "/");
  server.send(303);
  delay(100);
}

void handle_not_found(){
  server.send(404, "text/html", "404: check URL");
}

void server_init() {
  server.on("/", HTTP_GET, handle_root);
  server.on("/wifi", HTTP_POST, handle_wifi);
  server.onNotFound(handle_not_found);

  server.begin();
  Serial.print("Server tarted on port ");
  Serial.println(WEB_SERVER_PORT);
}