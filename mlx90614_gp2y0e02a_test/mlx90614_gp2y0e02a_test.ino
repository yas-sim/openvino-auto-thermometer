#include <Adafruit_MLX90614.h>

Adafruit_MLX90614 mlx = Adafruit_MLX90614();

#define DIST_SENSOR_PIN (10)

void setup() {
  pinMode(DIST_SENSOR_PIN, INPUT);
  Serial.begin(115200);
  mlx.begin();
  mlx.writeEmissivity(0.98);    // Emissivity of human skin
  Serial.print("Current emissivity = "); Serial.println(mlx.readEmissivity());
}

float readDist(void) {
    uint16_t dist_read = analogRead(DIST_SENSOR_PIN);
    // GP2Y0E02A   10cm = 2.0V, 50cm=0.55V
    const float v10 = (1.32f*1024.f)/3.3f;    // 10cm = 1.32V
    const float v30 = (0.76f*1024.f)/3.3f;    // 30cm = 0.76V
    const float grad = (10.f-30.f)/(v10-v30);
    const float intersect = 10 - (v10 * grad);   // 65.1838 (distance @ v=0)
    float dist = (float)dist_read * grad + intersect;
    return dist;
}

void loop() {
  float temp_amb = mlx.readAmbientTempC();
  float temp_obj = mlx.readObjectTempC();
  float dist = readDist();
#if 0
  String line1, line2;
  line1 = String(temp_obj, 1);
  line1 += "[C]";
  line2 = "Ambient: ";
  line2 += String(temp_amb, 1);
  line2 += "[C]";
  Serial.println(line1);
  Serial.println(line2);
  Serial.print("Distance = ");
  Serial.println(dist);
#else
  if(dist>=4.0f && dist<=6.5f) {
    String msg;
    msg = "Dist:";
    msg += String(dist, 1);
    msg += "  Obj:";
    msg += String(temp_obj, 1);
    msg += "[C]  Amb:";
    msg += String(temp_amb, 1);
    msg += "[C]";
    Serial.println(msg);   
  }
#endif
  delay(300);
}
