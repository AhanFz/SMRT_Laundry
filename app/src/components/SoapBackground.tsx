// app/src/components/SoapBackground.tsx
import React from "react";
import { View } from "react-native";
import Svg, { Defs, LinearGradient, Stop, Rect, Circle } from "react-native-svg";

export default function SoapBackground() {
  return (
    <View style={{ position: "absolute", inset: 0 }}>
      <Svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
        <Defs>
          {/* stronger sky-blue gradient */}
          <LinearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0%" stopOpacity="1" stopColor="#d6edff" />
            <Stop offset="50%" stopOpacity="1" stopColor="#eef7ff" />
            <Stop offset="100%" stopOpacity="1" stopColor="#ffffff" />
          </LinearGradient>
        </Defs>
        <Rect x="0" y="0" width="100" height="100" fill="url(#bg)" />
        {/* crisp white bubbles (less opacity than before) */}
        <Circle cx="14" cy="10" r="4.5" fill="#ffffff" opacity="0.85" />
        <Circle cx="22" cy="18" r="2.6" fill="#ffffff" opacity="0.8" />
        <Circle cx="86" cy="22" r="5.5" fill="#ffffff" opacity="0.8" />
        <Circle cx="92" cy="31" r="2.4" fill="#ffffff" opacity="0.8" />
        <Circle cx="10" cy="74" r="6.5" fill="#ffffff" opacity="0.8" />
        <Circle cx="20" cy="82" r="3.2" fill="#ffffff" opacity="0.8" />
        <Circle cx="88" cy="80" r="5.5" fill="#ffffff" opacity="0.8" />
      </Svg>
    </View>
  );
}
