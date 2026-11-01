extern "C" int func_60169328(const char *o) {
    if (*(const unsigned char *)(o + 0x5) == 0)
        return 0;
    const float f = *(const float *)(o + 0x5c);
    int r;
    if (!(f > 0.0f))
        r = 1;
    else
        r = 0;
    return r;
}