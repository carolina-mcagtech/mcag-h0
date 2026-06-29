"use client"
import { useEffect, useRef } from "react"
import { cn } from "@/lib/utils"

interface AddressAutocompleteProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  disabled?: boolean
}

export function AddressAutocomplete({
  value,
  onChange,
  placeholder = "Property address",
  className,
  disabled,
}: AddressAutocompleteProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null)

  function initAutocomplete() {
    if (!inputRef.current || autocompleteRef.current) return
    if (!window.google?.maps?.places) return
    autocompleteRef.current = new window.google.maps.places.Autocomplete(
      inputRef.current,
      {
        types: ["address"],
        componentRestrictions: { country: "us" },
        fields: ["formatted_address"],
      }
    )
    autocompleteRef.current.addListener("place_changed", () => {
      const place = autocompleteRef.current?.getPlace()
      if (place?.formatted_address) {
        onChange(place.formatted_address)
      }
    })
  }

  // Handle case where Google Maps already loaded (modal reopen)
  useEffect(() => {
    if (window.google?.maps?.places) {
      initAutocomplete()
    }
  }, [])

  // Expose initAutocomplete for the Script onLoad callback
  useEffect(() => {
    (window as unknown as Record<string, unknown>)["initGoogleMapsAutocomplete"] = initAutocomplete
    return () => {
      delete (window as unknown as Record<string, unknown>)["initGoogleMapsAutocomplete"]
    }
  }, [onChange])

  return (
    <input
      ref={inputRef}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      disabled={disabled}
      autoComplete="off"
      className={cn(
        "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
    />
  )
}
