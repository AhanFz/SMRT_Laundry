// app/src/components/MessageBubble.tsx
import React from "react";
import { View, Platform } from "react-native";
import { Text } from "react-native-paper";

type Props = { role: "user" | "assistant"; text: string };

const mono = Platform.select({ ios: "Menlo", android: "monospace", default: "monospace" });

export default function MessageBubble({ role, text }: Props) {
  const isUser = role === "user";
  return (
    <View
      style={{
        alignSelf: isUser ? "flex-end" : "flex-start",
        maxWidth: "92%",
        backgroundColor: isUser ? "#0A66C2" : "#FFFFFF", // deep blue vs white
        borderRadius: 14,
        paddingVertical: 10,
        paddingHorizontal: 12,
        marginVertical: 6,
        borderWidth: isUser ? 0 : 1,
        borderColor: "#D6E3F3",
      }}
    >
      <Text
        style={{
          color: isUser ? "#FFFFFF" : "#0B2948",
          fontSize: 15,
          lineHeight: 22,
          fontFamily: isUser ? undefined : mono, // assistant answers look more "data/CLI"-like
        }}
      >
        {text}
      </Text>
    </View>
  );
}
