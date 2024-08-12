clc 
clear

file = fopen("C:\Users\luizv\Desktop\square_0.bin",'r');
data_raw = fread(file);
data_hex = dec2hex(data_raw);
fclose(file);

% Number of bytes per sample
num_bytes_per_sample = 27;
% Number of channels
num_channels = 8;
% Total number of samples
num_samples = length(data_raw) / num_bytes_per_sample;

% Reshape the data into 27-byte samples
data_hex = reshape(data_hex', num_bytes_per_sample*2, num_samples)';

% Extract channel data (skip the first 3 bytes which are the status word)
channel_data = data_hex(:, 7:end);

% Reshape channel data into 8 columns, 6 hex characters per column
channel_data = reshape(channel_data, num_samples, num_channels, 6);

% Convert the hex data directly to integers
int_data = hex2dec(reshape(channel_data, num_samples*num_channels, 6));

% Reshape back to samples x channels
int_data = reshape(int_data, num_samples, num_channels);

% Handle two's complement for 24-bit signed data
sign_mask = int_data >= 2^23;
int_data(sign_mask) = int_data(sign_mask) - 2^24;

% Convert to voltages
volt_data = int_data * 7.9473e-8;

% Define sampling rate (in Hz)
sampling_rate = 1000; % Example value, replace with actual rate
time = (0:num_samples-1) / sampling_rate;

% Plot each channel
figure;
for channel = 1:num_channels
    subplot(num_channels, 1, channel);
    plot(time, volt_data(:, channel));
    title(['Channel ' num2str(channel)]);
    xlabel('Time (s)');
    ylabel('Voltage (V)');
end

% Adjust layout
tightfig;

