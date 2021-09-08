/*----------------------------------------------
 *  M5Stack THermoImagge64 (AMG8833) Sample Program.
 *    #2019/12/22 - #2019/12/24 - #2020/04/27
 *    used Library   Adafruit_AMG88xx 
 *    Board Select -> M5Stack-core
  -----------------------------------------------*/
#include <M5Stack.h>
#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_AMG88xx.h>

#define SPEAKER_PIN    25
#define AMG88_ADDR   0x69       // AMG8833 I2c addr.(0x68 or 0x69)

#define LCDWIDTH    320
#define LCDHEIGHT   240
#define ILCDBRIGHT  128

#define SETUP_MODE    0       // Display Mao Mode
#define SETUP_TEMP    1       // Temp Center
#define SETUP_RANGE   2       // Temp Range
#define SETUP_ALART1  3       // Temp Alart1 (Mean-RED)
#define SETUP_ALART2  4       // Temp Alart2 (Peak-GREEN)
#define SETUP_DIR     5       // Sensor Direction (0:Normal   1:Face)
#define SETUP_MAX     6

#define MAPX       8
#define MAPY       8

#define IGRIDMAX    56
#define IGRIDMAX1   2
#define IGRIDMAX2   54
#define IAUTOMEMN   10
#define MAPWIDTH    224
#define RIGHTSPX    224
#define RIGHTWIDTH  96
#define IDIVMATRIX  7
#define fDIVMATRIX  (float)IDIVMATRIX


static unsigned long pretime;
static  int   sampledelay;        // Interval (ms)
static  int   alartTemp1;         // Mean Alart
static  int   alartTemp2;         // Peak Alart
static  int   centerTemp;
static  int   widthTemp;
static  byte  initFlag;    
static  byte  swmode;              // 0:temp   1:range    2:mode
static  byte  alartStatus;         // 0:Normal   1:alart1   2:alart2
static  byte  maptype;             // 0:Ary   1:Map   2:Auto
static  byte  sensdir;             // Sensor Direction (0:Normal   1:Face)
static  byte  autoptr;
static  int   automin[IAUTOMEMN];
static  int   automax[IAUTOMEMN];
static  uint16_t  color16[16];

static  float sensData[MAPX+1][MAPY+1];
static  float fMap[IGRIDMAX+1][IGRIDMAX+1];

void  SubUpdateMap();
void  SubCheckThermoValue();
void  SubDrawModeCondition();
void  SubDrawAlartStatus();
void  SubDrawRangeStatus();

uint16_t getColor(uint8_t red, uint8_t green, uint8_t blue){
  return ((red>>3)<<11) | ((green>>2)<<5) | (blue>>3);
}

Adafruit_AMG88xx amg;

void setup() {
int  radius,xa,ya,xa1,ya1;
  
    M5.begin();
    dacWrite(SPEAKER_PIN, 0); // Speaker OFF
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setTextColor(GREEN);
    M5.Lcd.setTextSize(2);    
    M5.Lcd.setCursor(0, 0);
    M5.Lcd.setBrightness(ILCDBRIGHT);
    M5.Lcd.println("Thermo Image64 #2019/12/24");
//--- 省電力でWifiOFFする場合に下記入れる
    WiFi.mode(WIFI_OFF);
//--   
    amg.begin(AMG88_ADDR);    // Labrary Start
    sampledelay = 100;        // Interval (100ms)
//--       
    color16[0]  = getColor(  0,  0,192);
    color16[1]  = getColor(  0, 48,160);
    color16[2]  = getColor( 48, 76,176);
    color16[3]  = getColor( 80,128,192);
    color16[4]  = getColor(112,160,208);
    color16[5]  = getColor(144,176,224);
    color16[6]  = getColor(160,224,240);
    color16[7]  = getColor(192,255,255);
    color16[8]  = getColor(255,255,112);
    color16[9]  = getColor(255,192,  0);
    color16[10] = getColor(255,144,  0);
    color16[11] = getColor(240,112,  0);
    color16[12] = getColor(240, 80,  0);
    color16[13] = getColor(208, 48,  0);
    color16[14] = getColor(160,  0,  0);
    color16[15] = getColor(255,  0,  0);
  //-- Mask Set.
    initFlag   = 1;    
    swmode     = 0;            // 0:temp   1:range    2:mode
    maptype    = 1;            // 0:Ary   1:Map    2:Auto
    sensdir    = 1;             // Sensor Direction (0:Normal   1:Face)
    centerTemp = 14;
    widthTemp  = 16;
    alartTemp1 = 25;         // Mean Alart
    alartTemp2 = 16;         // Peak Alart
    alartStatus= 0;          // 0:Normal   1:alart1   2:alart2
    autoptr    = 0;
    pretime    = millis()+sampledelay+2000;
}


void loop() {
  SubCheckThermoValue();        // 温度取得と表示
//-- キーボタンの確認
  M5.update();  
  if(M5.BtnA.wasPressed()){
    swmode++;              // 0:temp   1:range    2:mode
    if (swmode>=SETUP_MAX) swmode=0;
    SubDrawModeCondition();
  }
  if(M5.BtnB.wasPressed()){
    switch(swmode){
      case SETUP_TEMP:       // Temp DN
        centerTemp--;
        if (centerTemp<4) centerTemp=4;
        break;
      case SETUP_RANGE:       // Width DN
        widthTemp--;
        if (widthTemp<2) widthTemp=2;
        break;
      case SETUP_ALART1:    
        alartTemp1--;
        if (alartTemp1<5) alartTemp1=5;
        break;
      case SETUP_ALART2:    
        alartTemp2--;
        if (alartTemp2<5) alartTemp2=5;
        break;
      case SETUP_MODE:       // Map Mode
        if (maptype>0) maptype--;
        initFlag=1;
        break;
      case SETUP_DIR:       // Sensor Direction (0:Normal   1:Face)
        if (sensdir>0) sensdir--;
        break;
        
    }
    SubDrawModeCondition();
  }
//--  
  if(M5.BtnC.wasPressed()){
    switch(swmode){
      case SETUP_TEMP:       // Temp UP
        centerTemp++;
        if (centerTemp>60) centerTemp=60;
        break;
      case SETUP_RANGE:       // Width UP
        widthTemp++;
        if (widthTemp>20) widthTemp=20;
        break;
      case SETUP_ALART1:    
        alartTemp1++;
        if (alartTemp1>60) alartTemp1=60;
        break;
      case SETUP_ALART2:    
        alartTemp2++;
        if (alartTemp2>60) alartTemp2=60;
        break;
      case SETUP_MODE:       // Map Mode
        maptype++;
        if (maptype>2) maptype=0;
        initFlag=1;
        break;
      case SETUP_DIR:       // Sensor Direction (0:Normal   1:Face)
        sensdir++;
        if (sensdir>1) sensdir=0;
        break;
    }
    SubDrawModeCondition();
  }
}


//------------------------
//  Check Thermo Data
//  
void  SubCheckThermoValue(){
float   pixels[AMG88xx_PIXEL_ARRAY_SIZE];
unsigned long nowtime;
int      sel,x1,y1;

  nowtime    = millis();
  if (nowtime>=pretime){
    amg.readPixels(pixels);   
    sel = 0;
    for (y1=0; y1<MAPY; y1++){
      switch(sensdir){
        case 0:     // Normal
          for (x1=0; x1<MAPY; x1++){
            sensData[x1][y1] = pixels[sel++];
          }
          break;
        case 1:     // Face
          for (x1=0; x1<MAPY; x1++){
            sensData[7-x1][y1] = pixels[sel++];
          }
          break;
      }
    }
    SubUpdateMap();
    pretime  = nowtime+sampledelay;
  }
}
     

//---------------------
//  Update Thermo Map Image
//--------------------
void  SubUpdateMap(){
byte      x1,y1,sts;
int       val,n,m,xa,ya,xs,ys,mstart,mstop,nstart,nstop,dotsize,nMin,nMax,nMean;
float     fX,fY,fDiff,fSum,fMean,fFnX,fFnY,fMin,fScale,fRange,fMinData,fMaxData;

  if (initFlag>0){
    initFlag=0;
    M5.Lcd.fillScreen(BLACK);
    SubDrawModeCondition();
  }
//-- 
  fMinData=sensData[0][0];
  fMaxData=fMinData;
  fSum    = (float)0;
  for (x1=0; x1<MAPX; x1++){
    for (y1=0; y1<MAPX; y1++){
      fX = sensData[x1][y1];
      fSum = fSum+fX;
      if (fMinData>fX) fMinData=fX;
      if (fMaxData<fX) fMaxData=fX;
    }          
  }
  fMean = fSum/(float)(MAPX*MAPY);
  nMin  = (int)fMinData;
  nMax  = (int)fMaxData;
  nMean = (int)fMean;
  automin[autoptr] = nMin;
  automax[autoptr] = nMax;
  autoptr++;
  if (autoptr>=IAUTOMEMN) autoptr=0;
//-- Alart Check
  sts = 0;
  if (nMean>=alartTemp1){
    sts = 1;        // Alart1(RED)
  }else{
    if (nMax>=alartTemp2){
      sts = 2;        // Alart2(GREEN)
    }
  }
  if (alartStatus!=sts){
    alartStatus=sts;
    SubDrawAlartStatus();
  }
//-- Draw
  fMin = (float)(centerTemp-widthTemp/2);
  fScale = (float)widthTemp;
  fRange = (float)16;
//--
  switch(maptype){
    case 0:       // Ary
      dotsize = 224/8;
      for (ya=0; ya<MAPY; ya++){
        ys = dotsize*ya;
        for (xa=0; xa<MAPX; xa++){
          xs = dotsize*xa;
          val = (int)((sensData[xa][ya]-fMin)*fRange/fScale);
          if (val<0) val=0;
          if (val>=15) val=15;
          M5.Lcd.fillRect(xs,ys,dotsize,dotsize, color16[val]);   // 変数や配列にするとコンパイルエラー
        }
      }
      break;
    case 1:       // MAP
    case 2:       // AUTO
      if (maptype==2){
        nMin=0;
        nMax=0;
        for (x1=0; x1<IAUTOMEMN; x1++){
          nMin = nMin+automin[x1];
          nMax = nMax+automax[x1];
        }
        nMin = nMin/IAUTOMEMN-1;
        if (nMin<0) nMin=0;
        nMax = nMax/IAUTOMEMN+1;
        fMin = (float)nMin;
        fScale = (float)(nMax-nMin);
        if (fScale<(float)4) fScale=(float)4;
      }
      dotsize = 4;
      for (ya=IGRIDMAX1; ya<IGRIDMAX2; ya++){
        fY = (float)ya/fDIVMATRIX-(float)0.4;
        mstart = (ya-IDIVMATRIX-1)/IDIVMATRIX;
        mstop  = (ya+IDIVMATRIX+1)/IDIVMATRIX;
        if (mstart<0) mstart=0;
        if (mstop<0)  mstop=0;
        if (mstart>=IGRIDMAX) mstart=IGRIDMAX-1;
        if (mstop>=IGRIDMAX)  mstop=IGRIDMAX-1;
      //--
        for (xa=IGRIDMAX1; xa<IGRIDMAX2; xa++){
          fSum = (float)0;
          fX = (float)xa/(float)fDIVMATRIX-(float)0.4;
          nstart = (xa-IDIVMATRIX-1)/IDIVMATRIX;
          nstop  = (xa+IDIVMATRIX+1)/IDIVMATRIX;
          if (nstart<0) nstart=0;
          if (nstop<0)  nstop=0;
          if (nstart>=IGRIDMAX) nstart=IGRIDMAX-1;
          if (nstop>=IGRIDMAX) nstop=IGRIDMAX-1;
          for (n=nstart; n<=nstop; n++){
            fDiff = (float)n-fX;
            if (fDiff<(float)0) fDiff=-fDiff;
            if (fDiff<=(float)1){
              fFnX = (float)1-fDiff;
              for (m=mstart; m<=mstop; m++){
                fDiff = (float)m-fY;
                if (fDiff<(float)0) fDiff=-fDiff;
                if (fDiff<=(float)1){
                  fFnY = (float)1-fDiff;
                  fSum = fSum+(sensData[n][m]*fFnX*fFnY);
                }
              }
            }
          }
          fMap[xa][ya] = fSum;
        }
      }
    //--
      for (ya=IGRIDMAX1; ya<IGRIDMAX2; ya++){
        ys = dotsize*(ya-IGRIDMAX1);
        for (xa=IGRIDMAX1; xa<IGRIDMAX2; xa++){
          xs = dotsize*(xa-IGRIDMAX1);
          val = (int)((fMap[xa][ya]-fMin)*fRange/fScale);
          if (val<0) val=0;
          if (val>=15) val=15;
          M5.Lcd.fillRect(xs,ys,dotsize,dotsize, color16[val]); 
        }
      }
      break;
  }
  M5.Lcd.fillRect(RIGHTSPX,32,RIGHTWIDTH,64, BLACK);
  M5.Lcd.setCursor(RIGHTSPX, 32);
  M5.Lcd.setTextSize(3);    
  M5.Lcd.print(sensData[3][4]);
  M5.Lcd.setTextSize(2);    
  M5.Lcd.setCursor(RIGHTSPX, 64);
  M5.Lcd.print("min");
  M5.Lcd.print(fMinData);
  M5.Lcd.setCursor(RIGHTSPX, 80);
  M5.Lcd.print("max");
  M5.Lcd.print(fMaxData);
 
}

//----------------------
//    Map Color Range
//----------------------
void  SubDrawRangeStatus(){
byte    i; 
 
  M5.Lcd.fillRect(0, 240-24, RIGHTSPX,16, BLACK);
  for (i=0; i<16; i++){
    M5.Lcd.fillRect(24+i*(RIGHTSPX-48)/16,240-15,(RIGHTSPX-48)/16,13, color16[i]);
  }
  M5.Lcd.setCursor(0, 240-16);
  M5.Lcd.print(centerTemp-widthTemp/2);
  M5.Lcd.setCursor(RIGHTSPX-16, 240-16);
  M5.Lcd.print(centerTemp+widthTemp/2);
}


//----------------------
//    Temp. Alart Display
//----------------------
void  SubDrawAlartStatus(){
  M5.Lcd.fillRect(RIGHTSPX,0,RIGHTWIDTH,32, BLACK);
  M5.Lcd.setTextSize(3);    
  M5.Lcd.setCursor(RIGHTSPX, 0);
  switch(alartStatus){
    case 0:
      M5.Lcd.setTextColor(GREEN);
      M5.Lcd.print(" OK ");
      break;
    case 1:
      M5.Lcd.setTextColor(RED);
      M5.Lcd.print("ALART");
      break;
    case 2:
      M5.Lcd.setTextColor(BLUE);
      M5.Lcd.print("FIND");
      break;
  }
  M5.Lcd.setTextSize(2);    
  M5.Lcd.setTextColor(GREEN);
}

//------------------------
//  Setup Mode 
//----------------------
void  SubDrawModeCondition(){
  M5.Lcd.setTextColor(GREEN);
  M5.Lcd.fillRect(RIGHTSPX,176,RIGHTWIDTH,64, BLACK);
  switch(swmode){
    case SETUP_TEMP:       // Temp/width
      M5.Lcd.setCursor(RIGHTSPX, 176);
      M5.Lcd.print("Temp");
      M5.Lcd.setCursor(RIGHTSPX, 176+16);
      M5.Lcd.print(centerTemp);
      M5.Lcd.setCursor(RIGHTSPX, 176+32);
      M5.Lcd.print((centerTemp-widthTemp/2));
      M5.Lcd.print("-");
      M5.Lcd.print((centerTemp+widthTemp/2));
      break;
    case SETUP_RANGE:       // Width UP
      M5.Lcd.setCursor(RIGHTSPX, 176);
      M5.Lcd.print("Range");
      M5.Lcd.setCursor(RIGHTSPX, 176+16);
      M5.Lcd.print(widthTemp);
      M5.Lcd.setCursor(RIGHTSPX, 176+32);
      M5.Lcd.print((centerTemp-widthTemp/2));
      M5.Lcd.print("-");
      M5.Lcd.print((centerTemp+widthTemp/2));
      break;
    case SETUP_ALART1:
      M5.Lcd.setCursor(RIGHTSPX, 176);
      M5.Lcd.print("Alart1");
      M5.Lcd.setCursor(RIGHTSPX, 176+16);
      M5.Lcd.print("(Mean)");
      M5.Lcd.setCursor(RIGHTSPX, 176+32);
      M5.Lcd.print(alartTemp1);
      break;
    case SETUP_ALART2:
      M5.Lcd.setCursor(RIGHTSPX, 176);
      M5.Lcd.print("Alart2");
      M5.Lcd.setCursor(RIGHTSPX, 176+16);
      M5.Lcd.print("(Peak)");
      M5.Lcd.setCursor(RIGHTSPX, 176+32);
      M5.Lcd.print(alartTemp2);
      break;
    case SETUP_MODE:       // Map Mode
      M5.Lcd.setCursor(RIGHTSPX, 176);
      M5.Lcd.print("Mode");
      M5.Lcd.setCursor(RIGHTSPX, 176+16);
      switch(maptype){
        case 0:
          M5.Lcd.print("Array");
          break;
        case 1:
          M5.Lcd.print("Map");
          break;
        case 2:
          M5.Lcd.print("Auto");
          break;
      }
      break;
    case SETUP_DIR:      // Sensor Direction (0:Normal   1:Face)
      M5.Lcd.setCursor(RIGHTSPX, 176);
      M5.Lcd.print("Dir");
      M5.Lcd.setCursor(RIGHTSPX, 176+16);
      switch(sensdir){
        case 0:
          M5.Lcd.print("Normal");
          break;
        case 1:
          M5.Lcd.print("Face");
          break;
      }
      break;
  }
  SubDrawRangeStatus();
  SubDrawAlartStatus();
}


//--- END --
