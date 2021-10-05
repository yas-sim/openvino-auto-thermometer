#define DIST_SENSOR_PIN (10)

void setup() {
  // put your setup code here, to run once:
    Serial.begin(115200);
    pinMode(DIST_SENSOR_PIN, INPUT);    // IR distance sensor
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
  // put your main code here, to run repeatedly:
    float dist = readDist();
    Serial.print("Distance = ");
    Serial.println(dist);

    delay(300);
}
