import React from "react";
import { View, Image } from "react-native";
import { Text } from "react-native-paper";

type Props = { name: string; price?: number };

export default function PriceRow({ name, price }: Props) {
  return (
    <View style={{
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      paddingVertical: 14
    }}>
      <View style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
        <View style={{ width: 40, height: 40, borderRadius: 8, backgroundColor: "#f4f6f8", alignItems:"center", justifyContent:"center" }}>
          {/* placeholder glyph */}
          <Text>👕</Text>
        </View>
        <Text variant="titleMedium">{name}</Text>
      </View>
      <Text variant="titleMedium">{price != null ? `$ ${price.toFixed(2)}` : "-"}</Text>
    </View>
  );
}
