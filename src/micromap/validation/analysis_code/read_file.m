clc 
clear

file = fopen("C:\Users\mcjpe\Desktop\test_0.bin",'r');
%fseek(file, -12800000000, "eof");
data_raw = fread(file, 'integer*2=>signed', 'ieee-le');
%data_char = fread(file, 'char', 'ieee-be');
fclose(file);

num_channels = 3;
data = reshape(data_raw, num_channels, []);

data = 0.195*data;

figure(1)
for a = 1:num_channels
    subplot(2,2, a)
    plot(data(a,:))
    %ylim([-1000, 1000])
end
hold on

% figure(2)
% for a = 17:32
%     subplot(8,2, a-16)
%     plot(data(a,:))
%     ylim([-35000, 35000])
% end
% hold on

%data_d = detrend(data_14, "constant");
%data_filtered = lowpass(data_d, 40, 2000);
%data_f = lowpass(data(5,:), 10, 1000);

% rng default
% 
% fs = 1000;
% t = 0:1/fs:5-1/fs;
% 
% [pxx,f] = pwelch(data(5,:),500,300,500,fs);
% 
% plot(f,10*log10(pxx))
% 
% xlabel('Frequency (Hz)')
% ylabel('PSD (dB/Hz)')

