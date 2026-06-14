import { Button, Stack, Typography, TextField, Switch, FormControlLabel, Box, Select, MenuItem, Divider } from "@mui/material";
import { useState } from "react";
import AddressAutocomplete from "./AddressAutocomplete";

export default function ControlPanel({
  depot,
  setDepot,
  endPoint,
  setEndPoint,
  trucks,
  setTrucks,
  onOptimizeRoute,
  instructions = [] as any[][],
}) {
  const [depotAddress, setDepotAddress] = useState("");
  const [endPointAddress, setEndPointAddress] = useState("");
  const [useDifferentEndPoint, setUseDifferentEndPoint] = useState(false);
  const [mode, setMode] = useState("custom");
  const [numRandomPoints, setNumRandomPoints] = useState(5);
  const [activeTruckIdx, setActiveTruckIdx] = useState(0);

  const activeTruck = trucks[activeTruckIdx];

  const handleUpdateDepot = (val: string) => setDepotAddress(val);
  const handleUpdateEndPoint = (val: string) => setEndPointAddress(val);

  const handleCollectionAddressChange = (index: number, val: string) => {
    const newTrucks = [...trucks];
    newTrucks[activeTruckIdx].addresses[index] = val;
    setTrucks(newTrucks);
  };

  const handleCollectionPointSelected = (index: number, point: { lat: number, lng: number }) => {
    const newTrucks = [...trucks];
    newTrucks[activeTruckIdx].points[index] = point;
    setTrucks(newTrucks);
  };

  const addCollectionField = () => {
    const newTrucks = [...trucks];
    newTrucks[activeTruckIdx].addresses.push("");
    setTrucks(newTrucks);
  };

  const addNewTruck = () => {
    const newId = `Truck ${trucks.length + 1}`;
    setTrucks([...trucks, { id: newId, points: [], addresses: [""] }]);
    setActiveTruckIdx(trucks.length);
  };

  return (
    <Stack spacing={1.5} sx={{ p: 1 }}>
      <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Route Planner</Typography>

      <Box sx={{ borderLeft: '2px solid #1976d2', pl: 1, ml: 1 }}>
        <AddressAutocomplete
          label="Start point"
          value={depotAddress}
          onAddressChange={handleUpdateDepot}
          onPointSelected={(pt) => setDepot(pt)}
        />

        <FormControlLabel
          control={<Switch size="small" checked={useDifferentEndPoint} onChange={(e) => {
            setUseDifferentEndPoint(e.target.checked);
            if (!e.target.checked) setEndPoint(null); // Reset end point when toggled off
          }} />}
          label={<Typography variant="body2" sx={{ fontSize: '0.8rem' }}>Different end point?</Typography>}
          sx={{ mb: 1 }}
        />

        {useDifferentEndPoint && (
          <AddressAutocomplete
            label="End point"
            value={endPointAddress}
            onAddressChange={handleUpdateEndPoint}
            onPointSelected={(pt) => setEndPoint(pt)}
          />
        )}
      </Box>

      <Divider sx={{ my: 1 }} />

      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="subtitle2">Fleets & Routes</Typography>
        <Button size="small" onClick={addNewTruck} sx={{ textTransform: 'none' }}>+ Add Truck</Button>
      </Stack>

      {trucks.length > 1 && (
        <Select
          size="small"
          value={activeTruckIdx}
          onChange={(e) => setActiveTruckIdx(Number(e.target.value))}
          sx={{ fontSize: '0.85rem' }}
        >
          {trucks.map((t: any, idx: number) => (
            <MenuItem key={idx} value={idx} sx={{ fontSize: '0.85rem' }}>{t.id}</MenuItem>
          ))}
        </Select>
      )}

      <Typography variant="subtitle2" sx={{ mt: 1 }}>Routing Mode ({activeTruck.id})</Typography>
      <Stack direction="row" spacing={1}>
        <Button size="small" variant={mode === "custom" ? "contained" : "outlined"} onClick={() => setMode("custom")}>
          Custom
        </Button>
        <Button size="small" variant={mode === "random" ? "contained" : "outlined"} onClick={() => setMode("random")}>
          Random
        </Button>
      </Stack>

      {mode === "random" && (
        <TextField
          label="Random Points Count"
          size="small"
          type="number"
          fullWidth
          value={numRandomPoints}
          onChange={(e) => setNumRandomPoints(parseInt(e.target.value) || 5)}
          sx={{ '& .MuiInputBase-root': { fontSize: '0.85rem' } }}
        />
      )}

      {mode === "custom" && (
        <Box sx={{ borderLeft: '2px solid #9e9e9e', pl: 1, ml: 1, mt: 1 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>Stops</Typography>
          {activeTruck.addresses.map((addr: string, idx: number) => (
            <AddressAutocomplete
              key={idx}
              label={`Stop ${idx + 1}`}
              value={addr}
              onAddressChange={(val) => handleCollectionAddressChange(idx, val)}
              onPointSelected={(pt) => handleCollectionPointSelected(idx, pt)}
            />
          ))}
          <Button 
            size="small" 
            onClick={addCollectionField}
            sx={{ textTransform: 'none', color: '#5f6368' }}
          >
            + Add destination
          </Button>
        </Box>
      )}

      <Button variant="contained" color="success" size="large" sx={{ mt: 2 }} onClick={() => onOptimizeRoute(mode, numRandomPoints)}>
        Optimize Route
      </Button>

      {instructions[activeTruckIdx] && instructions[activeTruckIdx].length > 0 && (
        <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #e0e0e0' }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>Turn-by-turn Instructions</Typography>
          <Box sx={{ maxHeight: 300, overflowY: 'auto', bgcolor: '#f5f5f5', p: 1, borderRadius: 1 }}>
            {instructions[activeTruckIdx].map((step: any, idx: number) => (
              <Box key={idx} sx={{ mb: 1, pb: 1, borderBottom: '1px solid #e0e0e0', '&:last-child': { borderBottom: 'none', mb: 0, pb: 0 } }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{step.instruction}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {step.length > 0 ? `${(step.length).toFixed(2)} km` : ""}
                  {step.length > 0 && step.time > 0 ? " • " : ""}
                  {step.time > 0 ? `${Math.ceil(step.time / 60)} min` : ""}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>
      )}
    </Stack>
  );
}
