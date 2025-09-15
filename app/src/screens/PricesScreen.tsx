import React, { useEffect, useMemo, useState } from "react";
import { View, FlatList } from "react-native";
import { ActivityIndicator, Card, Searchbar, Text, Divider, IconButton } from "react-native-paper";
import { Image } from "react-native";

const shirtIcon = require("../../assets/icons/shirt.png");
const pantsIcon = require("../../assets/icons/pants.png");
const shoesIcon = require("../../assets/icons/shoes.png");
const capIcon = require("../../assets/icons/cap.png");
const dressIcon = require("../../assets/icons/dress.png");
const jacketIcon = require("../../assets/icons/jacket.png");
const defaultIcon = require("../../assets/icons/default.png");

const ITEM_ICONS: Record<number, any> = {
  1: shirtIcon,
  2: pantsIcon,
  3: shoesIcon,
  4: jacketIcon,
  5: dressIcon,
  6: capIcon,
};


const API_BASE = process.env.EXPO_PUBLIC_API_BASE || "http://localhost:8000";

// Name-based icon map (case-insensitive match)
const ICONS_BY_NAME: Record<string, any> = {
  shirt: require("../../assets/icons/shirt.png"),
  pants: require("../../assets/icons/pants.png"),
  shoes: require("../../assets/icons/shoes.png"),
  jacket: require("../../assets/icons/jacket.png"),
  blazer: require("../../assets/icons/jacket.png"),
  dress: require("../../assets/icons/dress.png"),
  cap: require("../../assets/icons/cap.png"),
  washing: require("../../assets/icons/washing.png"),
  default: require("../../assets/icons/default.png"),
};


type PriceRow = { item_id: number; name: string; baseprice: number };

export default function PricesScreen() {
  const [data, setData] = useState<PriceRow[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);

  const limit = 25;
  const offset = page * limit;

  async function load() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(limit));
      params.set("offset", String(offset));
      if (q.trim()) params.set("q", q.trim());
      const res = await fetch(`${API_BASE}/pricelist?${params.toString()}`);
      const json = await res.json();
      if (!res.ok) throw new Error(json?.detail?.message || "Failed to load pricelist");
      setData(json.rows || []);
      setTotal(json.row_count || 0);
    } catch (e) {
      setData([]);
      setTotal(0);
      // Optional: you can display a toast/snackbar here
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  function getIconForName(name?: string): any {
    if (!name) return ICONS_BY_NAME.default;
    const key = name.toLowerCase();
  
    // Find first key that appears in the name
    const match = Object.keys(ICONS_BY_NAME).find((k) => key.includes(k));
    return match ? ICONS_BY_NAME[match] : ICONS_BY_NAME.default;
  }
  

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const pages = useMemo(() => Math.max(1, Math.ceil(total / limit)), [total]);

  return (
    <View style={{ flex: 1, padding: 12, backgroundColor: "#EEF7FF" }}>
      {/* header */}
      <View style={{ backgroundColor: "#0A66C2", paddingTop: 48, paddingBottom: 12, paddingHorizontal: 16, borderRadius: 12 }}>
        <Text variant="titleLarge" style={{ color: "#fff", fontWeight: "800" }}>
          Pricing
        </Text>
        <Text style={{ color: "#d9ecff" }}>Browse or search your price list.</Text>
      </View>

      {/* search */}
      <View style={{ marginTop: 12, marginBottom: 8, flexDirection: "row", gap: 8 }}>
        <Searchbar
          value={q}
          onChangeText={setQ}
          placeholder="search item name…"
          style={{ flex: 1, backgroundColor: "#fff" }}
          onSubmitEditing={() => {
            setPage(0);
            load();
          }}
        />
        <IconButton
          icon="magnify"
          mode="contained"
          containerColor="#0A66C2"
          iconColor="#fff"
          onPress={() => {
            setPage(0);
            load();
          }}
        />
      </View>

      {/* list */}
      {loading ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <ActivityIndicator color="#0A66C2" />
        </View>
      ) : (
        <Card style={{ flex: 1, backgroundColor: "#fff", borderRadius: 12 }}>
          <FlatList
            data={data}
            keyExtractor={(it) => String(it.item_id)}
            ItemSeparatorComponent={() => <Divider />}
            renderItem={({ item }) => (
              <View style={{ flexDirection: "row", alignItems: "center" }}>
                <Image
                //source={ITEM_ICONS[item.item_id] || require("../../assets/icons/default.png")}
                //source={ITEM_ICONS[item.item_id] || defaultIcon}
                source={getIconForName(item.name)}
                style={{ width: 32, height: 32, marginRight: 12 }}
              resizeMode="contain"
              />
  <View style={{ maxWidth: "70%" }}>
    <Text style={{ fontWeight: "800", color: "#0B2948" }}>{item.name}</Text>
    <Text style={{ color: "#557089" }}>ID: {item.item_id}</Text>
  </View>
</View>
            )}
            ListEmptyComponent={
              <View style={{ padding: 18 }}>
                <Text>No items found.</Text>
              </View>
            }
          />
        </Card>
      )}

      {/* pager */}
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 12, marginTop: 10 }}>
        <IconButton
          icon="chevron-left"
          disabled={page <= 0}
          onPress={() => setPage((p) => Math.max(0, p - 1))}
        />
        <Text>
          Page {pages === 0 ? 0 : page + 1} / {pages}
        </Text>
        <IconButton
          icon="chevron-right"
          disabled={(page + 1) >= pages}
          onPress={() => setPage((p) => p + 1)}
        />
      </View>
    </View>
  );
}
