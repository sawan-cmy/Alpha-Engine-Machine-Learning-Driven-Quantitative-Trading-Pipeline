// Live market data types for WebSocket messages

export interface QuoteData {
  symbol:     string;
  display:    string;
  sector:     string;
  price:      number | null;
  change:     number | null;
  change_pct: number | null;
  volume:     number | null;
  high:       number | null;
  low:        number | null;
  open:       number | null;
  prev_close: number | null;
  market_cap: number | null;
  updated_at: string;
  source:     string;
}

export interface QuoteUpdateMessage {
  type:      'quote_update';
  timestamp: string;
  data:      Record<string, QuoteData>;
}

export type WsMessage = QuoteUpdateMessage;

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface OhlcvPoint {
  date:   string;
  open:   number;
  high:   number;
  low:    number;
  close:  number;
  volume: number;
}
