#include <Servo.h>
#include <DHT.h>


Servo radarservo;
#define Servo_signal PA7
#define trig PA8
#define echo PA9

#define red1 PB4
#define red2 PB5
#define red3 PB6
#define green PB7
#define white PB8

const int allPins[] = {red1, red2, red3, green, white, trig};

#define DHTPIN PB0
#define DHTTYPE DHT11
DHT dht11(DHTPIN, DHTTYPE);

#define LDR PA2

int system_state = 0; // 0: OFF, 1: ON

float distance_time ,distance;
float celsius = 0;
int light;


unsigned long radar_prev_time = 0;
int radar_index = 0, radar_step = 10;


unsigned long temp_prev_time = 0;
unsigned long data_prev_time = 0;

void setup(){
  radarservo.attach(Servo_signal);
  pinMode(trig,OUTPUT);
  pinMode(echo,INPUT);
  pinMode(red1,OUTPUT);
  pinMode(red2,OUTPUT);
  pinMode(red3,OUTPUT);
  pinMode(green,OUTPUT);
  pinMode(white,OUTPUT);
  pinMode(DHTPIN,INPUT);
  pinMode(LDR,INPUT);
  dht11.begin();
  Serial.begin(9600);

  shutdownAll();
}

void loop(){
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == '1') {
      system_state = 1;
    } else if (cmd == '0') {
      system_state = 0;
      shutdownAll();
    }
  }
  
  if(system_state == 1){ // checks if the system is ON

    unsigned long current = millis();
    if(current - temp_prev_time >= 2000){ // Waits two seconds to read the temperature sensor
      temp_prev_time = current;
      float new_temp = dht11.readTemperature();

      if(!isnan(new_temp)){ // Handles temperature sensor error reading of NaN
        celsius = new_temp;
      }
    }

    distance = Read_Distance();
    light = light_intensity(); // 0: Low, 1: High

    control_led(celsius);
    
    Radar_system(distance);

    if (current - data_prev_time >= 1000) { // wait one second to send data
      data_prev_time = current;
      send_data(celsius, distance, light);
    }
    
  }
  
}



void control_led(float temp_val){
   if (temp_val<20){
    digitalWrite(red1,HIGH);
    digitalWrite(red2,LOW);
    digitalWrite(red3,LOW);
  }
  else if(temp_val>30){
    digitalWrite(red1,HIGH);
    digitalWrite(red2,HIGH);
    digitalWrite(red3,HIGH);
  }
  else{
    digitalWrite(red1,HIGH);
    digitalWrite(red2,HIGH);
    digitalWrite(red3,LOW);
  }
}



float light_intensity(){
  float light_val=analogRead(LDR);

  if(light_val<2045){
    digitalWrite(white,HIGH);
    light = 0; // low light intensity
  }else{
    digitalWrite(white,LOW);
    light = 1; // high light intensity
  }
  return light;
}

float Read_Distance(){
  digitalWrite(trig,LOW);
  delayMicroseconds(2);
  digitalWrite(trig,HIGH);
  delayMicroseconds(10);
  digitalWrite(trig,LOW);
  distance_time=pulseIn(echo,HIGH);
  distance=0.0343*(distance_time/2);
  return distance;

}

void Radar_system(float distance){

  unsigned long radar_current_time = millis();
  

  if(radar_current_time - radar_prev_time >= 100){
    radar_prev_time = radar_current_time;
    radarservo.write(radar_index);

    if(distance>0&&distance<10){
      digitalWrite(green,HIGH);
    }else{
      digitalWrite(green,LOW);    
    }

    radar_index+=radar_step;
    if(radar_index >= 180 || radar_index <= 0) {
      radar_step = -1*radar_step;
    }
    

  }

}

void send_data(float celsius, float distance, int light_state){

  Serial.print(String(celsius));
  Serial.print(",");
  Serial.print(String(distance));
  Serial.print(",");
  Serial.println(light_state);

}



void shutdownAll() {
  // Turn off all pins
  for (int i = 0; i < sizeof(allPins)/sizeof(allPins[0]); i++) {
    digitalWrite(allPins[i], LOW);
  }
  radarservo.write(0);  // Return servo to initial position
}