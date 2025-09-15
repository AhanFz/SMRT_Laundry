// app/src/screens/HomeScreen.tsx
import React from "react";
import { View, Pressable } from "react-native";
import { Text } from "react-native-paper";
import SoapBackground from "../components/SoapBackground";

type Props = { onStart: () => void };

const BLUE = "#0A66C2";

export default function HomeScreen({ onStart }: Props) {
  return (
    <View style={{ flex: 1, backgroundColor: "#fff", alignItems: "center" }}>
      {/* shared sky-blue gradient + a few SVG bubbles */}
      <SoapBackground />

      {/* extra background “foam” to fill the screen */}
      <View style={{ position: "absolute", top: 120, left: -30, width: 180, height: 180, borderRadius: 90, backgroundColor: "#ffffff", opacity: 0.25 }} />
      <View style={{ position: "absolute", top: 260, right: -20, width: 140, height: 140, borderRadius: 70, backgroundColor: "#ffffff", opacity: 0.22 }} />
      <View style={{ position: "absolute", bottom: 90, left: 30, width: 120, height: 120, borderRadius: 60, backgroundColor: "#ffffff", opacity: 0.18 }} />
      <View style={{ position: "absolute", bottom: 40, right: 20, width: 160, height: 160, borderRadius: 80, backgroundColor: "#ffffff", opacity: 0.2 }} />
      <View style={{ position: "absolute", top: 80, right: 110, width: 70, height: 70, borderRadius: 35, backgroundColor: "#ffffff", opacity: 0.28 }} />
      <View style={{ position: "absolute", top: 180, right: 70, width: 36, height: 36, borderRadius: 18, backgroundColor: "#ffffff", opacity: 0.3 }} />

      {/* wordmark */}
      <Text
        variant="headlineLarge"
        style={{ color: BLUE, fontWeight: "800", marginTop: 36, letterSpacing: 2 }}
      >
        SMRT
      </Text>

      {/* big blue ring button */}
      <Pressable
        onPress={onStart}
        accessibilityRole="button"
        style={({ pressed }) => ({
          marginTop: 28,
          width: 340,
          height: 340,
          borderRadius: 170,
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#fff",
          shadowColor: "#000",
          shadowOpacity: 0.18,
          shadowRadius: 28,
          shadowOffset: { width: 0, height: 14 },
          transform: [{ scale: pressed ? 0.98 : 1 }],
        })}
      >
        {/* outer ring */}
        <View
          style={{
            position: "absolute",
            width: 300,
            height: 300,
            borderRadius: 150,
            borderWidth: 12,
            borderColor: BLUE,
          }}
        />
        {/* copy inside the ring */}
        <Text style={{ color: "#9fbfe3", letterSpacing: 4, marginBottom: 6 }}>
          NEW ORDER
        </Text>
        <Text
          variant="headlineMedium"
          style={{ fontWeight: "800", color: "#1b3b63" }}
        >
          Open Chat
        </Text>
        <Text style={{ marginTop: 10, fontSize: 24, color: BLUE }}>→</Text>
      </Pressable>

      {/* removed the “refer credits” pill as requested */}
    </View>
  );
}
