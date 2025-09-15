import React, { useState } from "react";
import { View } from "react-native";
import { TextInput, Button, Card, Text } from "react-native-paper";
import ChartCard from "../components/ChartCard";
import { useApi } from "../hooks/useApi";
import { fmtCurrency } from "../utils/formatters";

export default function ReportsScreen() {
  const [cid, setCid] = useState("1001");
  const [report, setReport] = useState<any>(null);
  const { get, loading, error } = useApi();

  const load = async () => {
    try {
      const data = await get<any>(`/report/customer/${cid}`);
      setReport(data);
    } catch {
      // error is already set by the hook
    }
  };

  const revenue = report?.summary?.revenue;

  return (
    <View style={{ flex: 1, padding: 12 }}>
      <View style={{ flexDirection: "row", gap: 8 }}>
        <TextInput mode="outlined" style={{ flex: 1 }} value={cid} onChangeText={setCid} label="CID" />
        <Button mode="contained" onPress={load} disabled={loading}>Load</Button>
      </View>

      {error && <Text style={{ marginTop: 12 }}>Error: {error}</Text>}

      {report && (
        <>
          <Card style={{ marginTop: 12, padding: 12 }}>
            <Text variant="titleLarge">Summary</Text>
            <Text>Orders: {report.summary?.orders ?? "—"}</Text>
            <Text>Units: {report.summary?.units ?? "—"}</Text>
            <Text>Revenue: {fmtCurrency(revenue)}</Text>
            <Text selectable style={{ marginTop: 8 }}>
              SQL (summary): {report.sql.summary}
            </Text>
            <Text selectable>SQL (timeseries): {report.sql.timeseries}</Text>
          </Card>

          <ChartCard
            title="Revenue Over Time"
            data={report.timeseries || []}
            subtitle="Daily revenue aggregated from Inventory/Detail"
          />
        </>
      )}
    </View>
  );
}
