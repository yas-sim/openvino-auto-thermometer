#include <Adafruit_MLX90614.h>

Adafruit_MLX90614 mlx = Adafruit_MLX90614();

void setup() {
  Serial.begin(115200);
  mlx.begin();
  mlx.writeEmissivity(0.98);    // Emissivity of human skin
}

void loop() {
  Serial.print("Current emissivity = "); Serial.println(mlx.readEmissivity());
  String line1, line2;
  line1 = String(mlx.readObjectTempC(), 1);
  line1 += "[C]";
  line2 = "Ambient: ";
  line2 += String(mlx.readAmbientTempC(), 1);
  line2 += "[C]";

  Serial.println(line1);
  Serial.println(line2);

  delay(300);
}
