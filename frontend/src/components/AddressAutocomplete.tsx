import { useState, useEffect } from 'react';
import { Autocomplete, TextField } from '@mui/material';
import axios from 'axios';

export default function AddressAutocomplete({ 
  label, 
  value, 
  onAddressChange, 
  onPointSelected 
}: {
  label: string,
  value: string,
  onAddressChange: (val: string) => void,
  onPointSelected?: (point: { lat: number, lng: number }) => void
}) {
  const [options, setOptions] = useState<any[]>([]);
  const [inputValue, setInputValue] = useState(value);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  useEffect(() => {
    let active = true;

    if (!inputValue || inputValue.length < 3) {
      setOptions(value ? [{ display_name: value }] : []);
      return undefined;
    }

    const fetchOptions = async () => {
      try {
        const res = await axios.get("https://nominatim.openstreetmap.org/search", {
          params: {
            format: "json",
            q: `${inputValue}, Jena, Germany`,
            limit: 5,
          },
        });

        if (active) {
          setOptions(res.data);
        }
      } catch (e) {
        // Silently handle geocode fetch errors
      }
    };

    const debounceId = setTimeout(() => {
      fetchOptions();
    }, 500);

    return () => {
      active = false;
      clearTimeout(debounceId);
    };
  }, [inputValue, value]);

  return (
    <Autocomplete
      options={options}
      getOptionLabel={(option) => (typeof option === 'string' ? option : option.display_name || "")}
      filterOptions={(x) => x}
      value={value}
      onChange={(event, newValue: any) => {
        if (typeof newValue === 'string') {
          onAddressChange(newValue);
        } else if (newValue) {
          onAddressChange(newValue.display_name);
          if (onPointSelected && newValue.lat && newValue.lon) {
            onPointSelected({
              lat: parseFloat(newValue.lat),
              lng: parseFloat(newValue.lon)
            });
          }
        }
      }}
      onInputChange={(event, newInputValue, reason) => {
        if (reason === 'input') {
          setInputValue(newInputValue);
          onAddressChange(newInputValue);
        }
      }}
      renderInput={(params) => (
        <TextField {...params} label={label} size="small" fullWidth sx={{ mb: 1, '& .MuiInputBase-root': { fontSize: '0.85rem' } }} />
      )}
      isOptionEqualToValue={(option, val) => option.display_name === val}
    />
  );
}
