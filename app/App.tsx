import React, { useState } from "react";
import { View, Pressable } from "react-native";
import { PaperProvider, Text } from "react-native-paper";
import HomeScreen from "./src/screens/HomeScreen";
import ChatScreen from "./src/screens/ChatScreen";
import PricesScreen from "./src/screens/PricesScreen";

type Tab = "home" | "chat" | "pricing";

const TAB_BAR_HEIGHT = 68;

function Tabs({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  const TabBtn = ({ id, label, emoji }: { id: Tab; label: string; emoji: string }) => {
    const selected = active === id;
    return (
      <Pressable
        onPress={() => onChange(id)}
        style={{
          flex: 1,
          alignItems: "center",
          paddingVertical: 12,
          backgroundColor: selected ? "#0A66C2" : "#FFFFFF",
          borderRadius: 12,
          borderWidth: 2,
          borderColor: selected ? "#0A66C2" : "#C9D8EA",
        }}
      >
        <Text style={{ fontSize: 18, color: selected ? "#fff" : "#0B2948" }}>{emoji}</Text>
        <Text style={{ marginTop: 4, fontWeight: "700", color: selected ? "#fff" : "#0B2948" }}>{label}</Text>
      </Pressable>
    );
  };
  return (
    <View
    style={{
      position: "fixed" as any,
      left: 12,
      right: 12,
      bottom: 12,
      height: TAB_BAR_HEIGHT,
      backgroundColor: "#FFFFFF",
      borderRadius: 16,
      padding: 8,
      flexDirection: "row",
      gap: 10,
      borderWidth: 2,
      borderColor: "#C9D8EA",
      zIndex: 999,
      alignItems: "stretch",
    }}
  >
      <TabBtn id="home" label="Laundry" emoji="🧺" />
      <TabBtn id="chat" label="Chat" emoji="💬" />
      <TabBtn id="pricing" label="Pricing" emoji="💲" />
    </View>
  );
}

export default function App() {
  const [tab, setTab] = useState<Tab>("chat"); // start on chat
  return (
    <PaperProvider>
      {tab === "home" && <HomeScreen onStart={() => setTab("chat")} />}
      {tab === "chat" && <ChatScreen />}
      {tab === "pricing" && <PricesScreen />}

      <Tabs active={tab} onChange={setTab} />
    </PaperProvider>
  );
}
