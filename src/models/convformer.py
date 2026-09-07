import torch
import torch.nn as nn
import torch.nn.functional as F

class SpatialCNN(nn.Module):
    def __init__(self, in_channels=7, out_channels=64):
        super().__init__()
        # 2D CNN mapping input channels to latent features
        self.conv1 = nn.Conv2d(in_channels, 32, kernel_size=3, padding=1)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(32, out_channels, kernel_size=3, padding=1)
        
    def forward(self, x):
        # x: (B*T, C, H, W)
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        return x

class ConvLSTMCell(nn.Module):
    def __init__(self, input_dim, hidden_dim, kernel_size, bias=True):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size
        self.padding = kernel_size // 2
        
        self.conv = nn.Conv2d(in_channels=self.input_dim + self.hidden_dim,
                              out_channels=4 * self.hidden_dim,
                              kernel_size=self.kernel_size,
                              padding=self.padding,
                              bias=bias)
                              
    def forward(self, input_tensor, cur_state):
        h_cur, c_cur = cur_state
        combined = torch.cat([input_tensor, h_cur], dim=1)
        combined_conv = self.conv(combined)
        
        cc_i, cc_f, cc_o, cc_g = torch.split(combined_conv, self.hidden_dim, dim=1)
        i = torch.sigmoid(cc_i)
        f = torch.sigmoid(cc_f)
        o = torch.sigmoid(cc_o)
        g = torch.tanh(cc_g)
        
        c_next = f * c_cur + i * g
        h_next = o * torch.tanh(c_next)
        
        return h_next, c_next

class ConvLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, kernel_size=3):
        super().__init__()
        self.cell = ConvLSTMCell(input_dim, hidden_dim, kernel_size)
        
    def forward(self, x):
        # x: (B, T, C, H, W)
        b, seq_len, c, h, w = x.size()
        h_t = torch.zeros(b, self.cell.hidden_dim, h, w, device=x.device)
        c_t = torch.zeros(b, self.cell.hidden_dim, h, w, device=x.device)
        
        outputs = []
        for t in range(seq_len):
            h_t, c_t = self.cell(x[:, t, :, :, :], (h_t, c_t))
            outputs.append(h_t.unsqueeze(1))
            
        # (B, T, C, H, W)
        return torch.cat(outputs, dim=1)

class PatchEmbedding(nn.Module):
    def __init__(self, in_channels=64, embed_dim=256, patch_size=4):
        super().__init__()
        self.patch_size = patch_size
        self.proj = nn.Conv2d(in_channels, embed_dim, kernel_size=patch_size, stride=patch_size)
        
    def forward(self, x):
        # Pad from 101x241 to 104x244
        # padding format for F.pad is (left, right, top, bottom)
        # H=101 -> 104 (+3 bottom), W=241 -> 244 (+3 right)
        x_padded = F.pad(x, (0, 3, 0, 3))
        
        # x_padded: (B*T, C, H', W')
        x_patches = self.proj(x_padded) # (B*T, D, H'/4, W'/4) -> (B*T, 256, 26, 61)
        return x_patches

class Decoder(nn.Module):
    def __init__(self, embed_dim=256, out_channels=32, patch_size=4):
        super().__init__()
        # Upsample 26x61 -> 104x244
        self.upconv = nn.ConvTranspose2d(embed_dim, out_channels, kernel_size=patch_size, stride=patch_size)
        self.relu = nn.ReLU(inplace=True)
        self.conv = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        
    def forward(self, x):
        # x: (B*T, D, 26, 61)
        x = self.upconv(x) # (B*T, out_channels, 104, 244)
        x = self.relu(x)
        x = self.relu(self.conv(x))
        # Crop back to 101x241
        x = x[:, :, :101, :241]
        return x

class ConvFormer(nn.Module):
    def __init__(self, in_channels=7, out_channels=15, 
                 cnn_dim=64, embed_dim=128, 
                 transformer_layers=4, transformer_heads=4):
        super().__init__()
        self.cnn_dim = cnn_dim
        self.embed_dim = embed_dim
        
        self.spatial_cnn = SpatialCNN(in_channels, cnn_dim)
        self.conv_lstm = ConvLSTM(cnn_dim, cnn_dim, kernel_size=3)
        
        self.patch_embed = PatchEmbedding(in_channels=cnn_dim, embed_dim=embed_dim, patch_size=4)
        
        # Positional Encoding
        self.num_patches = 26 * 61 # 1586
        self.pos_embed = nn.Parameter(torch.randn(1, 1, self.num_patches, embed_dim))
        
        # Transformer
        encoder_layer = nn.TransformerEncoderLayer(d_model=embed_dim, nhead=transformer_heads, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=transformer_layers)
        
        # Decoder
        decoder_dim = 64
        self.decoder = Decoder(embed_dim=embed_dim, out_channels=decoder_dim, patch_size=4)
        
        # Projection
        self.projection = nn.Conv2d(decoder_dim, out_channels, kernel_size=1)
        
    def forward(self, x):
        # x: (B, T, C, H, W)
        b, t, c, h, w = x.size()
        
        # 1. CNN Feature Extractor
        x = x.view(b * t, c, h, w)
        cnn_out = self.spatial_cnn(x)
        
        # 2. ConvLSTM
        cnn_out = cnn_out.view(b, t, self.cnn_dim, h, w)
        lstm_out = self.conv_lstm(cnn_out) # (B, T, C', H, W)
        
        # 3. Patch Embedding
        lstm_out = lstm_out.view(b * t, self.cnn_dim, h, w)
        patches = self.patch_embed(lstm_out) # (B*T, D, 26, 61)
        
        # 4. Flatten & Positional Encoding
        _, d, ph, pw = patches.size()
        patches_flat = patches.flatten(2).transpose(1, 2) # (B*T, 1586, D)
        
        # Add temporal dimension for sequence processing if we wanted T in transformer,
        # but the spec says "Captures global basin teleconnections". 
        # Wait, the spec says "Flattening: The spatial tensor is flattened along height and width yielding length N. Input Sequence: (B, 5, N, D)".
        # It says "Input Sequence: (B, 5, N, D)". Does the transformer act on the N dimension or T?
        # Standard Vision Transformer applies self-attention across spatial patches.
        # Let's reshape to (B*5, N, D) and apply attention over N.
        
        patches_flat = patches_flat + self.pos_embed.squeeze(0) # broadcasting over B*T
        
        # 5. Transformer
        # PyTorch TransformerEncoder with batch_first=True expects (Batch, Seq, Feature)
        # Here Batch is B*T, Seq is N, Feature is D
        trans_out = self.transformer(patches_flat) # (B*T, 1586, D)
        
        # 6. Reshape
        trans_out = trans_out.transpose(1, 2).view(b * t, d, ph, pw) # (B*T, D, 26, 61)
        
        # 7. Decoder
        dec_out = self.decoder(trans_out) # (B*T, dec_dim, 101, 241)
        
        # 8. Projection
        out = self.projection(dec_out) # (B*T, 15, 101, 241)
        
        # Reshape back to (B, T, 15, 101, 241)
        out = out.view(b, t, -1, h, w)
        
        return out
