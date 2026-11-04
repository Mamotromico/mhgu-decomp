extern "C" int func_600e9f9c(const unsigned char* p, unsigned char v)
{
    for (int i = 0; i < 12; i++) {
        if (p[0x264 + i] == v) return 1;
    }
    return 0;
}