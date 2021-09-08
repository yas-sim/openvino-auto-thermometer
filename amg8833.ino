/*******************************************************************************
// SWITCHSCIENCE wiki -- http://trac.switch-science.com/
// AMG88 Arduino Sample
*******************************************************************************/
#include <Wire.h>

#define PCTL  (0x00)
#define RST   (0x01)
#define FPSC  (0x02)
#define INTC  (0x03)
#define STAT  (0x04)
#define SCLR  (0x05)
#define AVE   (0x07)
#define INTHL (0x08)
#define TTHL  (0x0E)
#define TTHH  (0x0F)
#define INT0  (0x10)
#define T01L  (0x80)

#define AMG88_ADDR 0x68 // in 7bit


void setup()
{
    Serial.begin(115200);
    Wire.begin();

    int tmp;
    tmp = 0x3f;
    datasend(AMG88_ADDR, RST, &tmp, 1);
    delay(1000);
    
    int fpsc = B00000000;// 1fps
    datasend(AMG88_ADDR,FPSC,&fpsc,1);
    int intc = 0x00; // diff interrpt mode, INT output reactive
    datasend(AMG88_ADDR,INTC,&intc,1);
    // moving average output mode active
    tmp = 0x50;
    datasend(AMG88_ADDR,0x1F,&tmp,1);
    tmp = 0x45;
    datasend(AMG88_ADDR,0x1F,&tmp,1);
    tmp = 0x57;
    datasend(AMG88_ADDR,0x1F,&tmp,1);
    tmp = 0x20;
    datasend(AMG88_ADDR,AVE,&tmp,1);
    tmp = 0x00;
    datasend(AMG88_ADDR,0x1F,&tmp,1);

    int sensorTemp[2];
    dataread(AMG88_ADDR,TTHL,sensorTemp,2);
    // 
    // Serial.print("sensor temperature:");
    // Serial.println( (sensorTemp[1]*256 + sensorTemp[0])*0.0625);
}

void datasend(int id,int reg,int *data,int datasize)
{
    Wire.beginTransmission(id);
    Wire.write(reg);
    for(int i=0;i<datasize;i++)
    {
        Wire.write(data[i]);
    }
    Wire.endTransmission();
}

void dataread(int id,int reg,int *data,int datasize)
{
    Wire.beginTransmission(id);
    Wire.write(reg);
    Wire.endTransmission(false);
    Wire.requestFrom(id, datasize, false);
    for(int i=0;i<datasize;i++)
    {
        data[i] = Wire.read();
    }
    Wire.endTransmission(true);
}

inline float translateTemp(uint16_t temp_val, float bit_weight) {
    float pos_neg = (temp_val & 0b0000100000000000) ? -1.f : 1.f;
    temp_val &= ~0b0000100000000000;
    float temp = (float)temp_val * bit_weight * pos_neg;
    return temp;
}

float readTemp() {
    int sensorTemp[2];
    dataread(AMG88_ADDR, TTHL, sensorTemp,2);
    uint16_t temp_i = (sensorTemp[1]<<8) | sensorTemp[0];
    return translateTemp(temp_i, 0.0625f);
}

void loop()
{
    float ambient = readTemp();   // Read ambient temperature
    Serial.print("@");
    Serial.println(ambient);
    Serial.println("[");
    // Wire library cannnot contain more than 32 bytes in bufffer
    // 2byte per one data
    // 2 byte * 16 data * 4 times
    int sensorData[32];
    for(int i = 0; i < 4; i++)
    {
        // read each 32 bytes 
        dataread(AMG88_ADDR, T01L + i*0x20, sensorData, 32);
        for(int l = 0 ; l < 16 ; l++)
        {
            int16_t temporaryData = (sensorData[l * 2 + 1] * 256 ) + sensorData[l * 2];
            float temperature = translateTemp(temporaryData, 0.25f);
            Serial.print(temperature);
            if( (l + i * 16)<63 ) Serial.print(",");
        }
        Serial.println();
    }
    Serial.println("]");
    
    delay(100);
}
