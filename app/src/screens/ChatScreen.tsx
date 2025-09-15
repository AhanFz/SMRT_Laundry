// app/src/screens/ChatScreen.tsx
import React, { useEffect, useRef, useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, View } from "react-native";
import { ActivityIndicator, IconButton, Text, TextInput } from "react-native-paper";
import SoapBackground from "../components/SoapBackground";
import MessageBubble from "../components/MessageBubble";

type Msg = { id: string; role: "user" | "assistant"; text: string };

const API_BASE = process.env.EXPO_PUBLIC_API_BASE || "http://localhost:8000";
const mono = Platform.select({ ios: "Menlo", android: "monospace", default: "monospace" });

// layout constants to keep everything from overlapping
const TAB_BAR_HEIGHT = 68;          // must match App.tsx Tabs
const INPUT_BAR_HEIGHT = 56;        // visual height of the input container
const OUTER_MARGIN = 12;            // outer spacing from screen edge
const GAP_ABOVE_TABS = 8;           // gap between input bar and tabs

// examples (updated CID)
const EXAMPLES = [
  "total revenue for CID: 1000001",
  "orders for cid: 1000001 between 2025-08-01 and 2025-08-03",
  "top customers by revenue",
  "price for item_id 30310",
];

export default function ChatScreen() {
  const [messages, setMessages] = useState<Msg[]>([
    { id: "hello", role: "assistant", text: "Hi! Type a query below (e.g., `top customers by revenue`)." },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  const scroller = useRef<ScrollView>(null);
  const inputRef = useRef<any>(null);

  // helper to always scroll to bottom
  const scrollToEnd = () => scroller.current?.scrollToEnd({ animated: true });

  useEffect(() => {
    // autofocus on web for CLI feel
    if (Platform.OS === "web") {
      const t = setTimeout(() => inputRef.current?.focus?.(), 200);
      return () => clearTimeout(t);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(scrollToEnd, 60);
    return () => clearTimeout(t);
  }, [messages.length, busy]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;

    setMessages((m) => [...m, { id: String(Date.now()), role: "user", text: trimmed }]);
    setInput("");
    setBusy(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed, limit: 50 }),
      });
      const json = await res.json();
      if (!res.ok) {
        const issues = Array.isArray(json?.detail?.issues) ? json.detail.issues.join("\n") : "";
        const errMsg = `${json?.detail?.message || "Failed to query"}${issues ? "\n" + issues : ""}`;
        setMessages((m) => [
          ...m,
          {
            id: String(Date.now() + 1),
            role: "assistant",
            text: `⚠️ ${errMsg}\n\nSQL:\n${json?.detail?.sql ?? ""}`,
          },
        ]);
      } else {
        const pretty =
          Array.isArray(json?.rows) && json.rows.length
            ? `✅ ${json.answer}\n\nSQL:\n${json.sql}\n\nFirst row:\n${JSON.stringify(json.rows[0], null, 2)}`
            : `ℹ️ ${json.answer}\n\nSQL:\n${json.sql}`;
        setMessages((m) => [...m, { id: String(Date.now() + 1), role: "assistant", text: pretty }]);
      }
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { id: String(Date.now() + 2), role: "assistant", text: `⚠️ ${e?.message || "Network error"}` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  // computed spaces so last message is never hidden
  const bottomInset = OUTER_MARGIN + TAB_BAR_HEIGHT + GAP_ABOVE_TABS + INPUT_BAR_HEIGHT;

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      // offset accounts for the fixed tab bar + our input bar
      keyboardVerticalOffset={TAB_BAR_HEIGHT + GAP_ABOVE_TABS + 8}
      style={{ flex: 1 }}
    >
      <View style={{ flex: 1 }}>
        <SoapBackground />

        {/* Header */}
        <View style={{ backgroundColor: "#0A66C2", paddingTop: 48, paddingBottom: 12, paddingHorizontal: 16 }}>
          <Text variant="titleLarge" style={{ color: "#fff", fontWeight: "800" }}>
            Laundry Assistant
          </Text>
          <Text style={{ color: "#d9ecff" }}>Ask about revenue, orders, items, pricing.</Text>
        </View>

        {/* Example cards */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={{ paddingHorizontal: 12, paddingTop: 10 }}
          contentContainerStyle={{ gap: 12, paddingBottom: 6 }}
        >
          {EXAMPLES.map((s) => (
            <View
              key={s}
              style={{
                width: 300,
                height: 200,
                borderRadius: 10,
                backgroundColor: "#EAF3FF",
                borderWidth: 2,
                borderColor: "#0A66C2",
                padding: 10,
                justifyContent: "space-between",
              }}
            >
              <Text style={{ color: "#0A66C2", fontWeight: "800" }}>{s}</Text>
              <Text
                onPress={() => send(s)}
                style={{
                  alignSelf: "flex-end",
                  color: "#fff",
                  backgroundColor: "#0A66C2",
                  paddingHorizontal: 10,
                  paddingVertical: 6,
                  borderRadius: 8,
                  fontWeight: "700",
                }}
              >
                Run →
              </Text>
            </View>
          ))}
        </ScrollView>

        {/* Messages */}
        <ScrollView
          ref={scroller}
          style={{ flex: 1, paddingHorizontal: 12, marginTop: 6 }}
          contentContainerStyle={{
            paddingTop: 6,
            paddingBottom: bottomInset + 24, // <- **key**: leave space for input+tabs
          }}
          onContentSizeChange={scrollToEnd}
          keyboardShouldPersistTaps="handled"
        >
          {messages.map((m) => (
            <MessageBubble key={m.id} role={m.role} text={m.text} />
          ))}
          {busy && (
            <View style={{ alignItems: "center", marginTop: 10 }}>
              <ActivityIndicator color="#0A66C2" />
            </View>
          )}
        </ScrollView>

        {/* CLI input bar (absolute, above tabs) */}
        <View
          style={{
            position: "absolute",
            left: OUTER_MARGIN + 4,
            right: OUTER_MARGIN + 4,
            bottom: OUTER_MARGIN + TAB_BAR_HEIGHT + GAP_ABOVE_TABS,
            height: INPUT_BAR_HEIGHT,
            backgroundColor: "#0B1B2B",
            borderRadius: 12,
            paddingHorizontal: 8,
            borderWidth: 2,
            borderColor: "#0A66C2",
            flexDirection: "row",
            alignItems: "center",
            zIndex: 1000,
          }}
        >
          <Text style={{ color: "#7FD1FF", fontFamily: mono, fontWeight: "700", marginHorizontal: 8 }}>{">"}</Text>
          <TextInput
            ref={inputRef}
            value={input}
            onChangeText={setInput}
            placeholder="type a query and press Enter…"
            placeholderTextColor="#8FA6BA"
            dense
            underlineColor="transparent"
            style={{
              flex: 1,
              backgroundColor: "transparent",
              color: "#E8F1F8",
              fontFamily: mono,
            }}
            onSubmitEditing={() => send(input)}
            blurOnSubmit={false}
            autoFocus={Platform.OS === "web"}
          />
          <IconButton
            icon="send"
            size={20}
            mode="contained"
            containerColor="#1E90FF"
            iconColor="#fff"
            onPress={() => send(input)}
          />
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}
