# AutoparkAutomata Parking Lot Control and Management System

Made for the Teknofest 2022 Smart Transportation Competition


<b>Important Note About 16x2 LCD Interaction</b>

To make use of a 16x2 LCD to display the empty spaces available in the parking lot, the following lines of code must be added to StandardFirmata on Arduino.

#include <LiquidCrystal.h>


//add to a non-setup non-loop part

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

int lastLine = 1;

void stringDataCallback(char *stringData){
   
   if ( lastLine ) {
     lastLine = 0;
     lcd.clear();
   } 
   
   else {
     lastLine = 1;
     lcd.setCursor(0,1);
   }
   lcd.print(stringData);
   
}

//add to void setup

lcd.begin(16,2);

Firmata.setFirmwareVersion( FIRMATA_MAJOR_VERSION, FIRMATA_MINOR_VERSION );

Firmata.attach( STRING_DATA, stringDataCallback);

Firmata.begin(); 


<b> Parts list of the complete system as used during the competition </b>

x1 Computer, of any sort.

x2 Micro Servos

x2 Webcams, or alternative cameras

x1 Arduino Uno

x1 JHD161A 16x2 LCD

x1 10K Potentiometer


