extern "C" int func_606b2118(const unsigned char *data, unsigned int bit) {
    return (data[bit >> 3] & (1u << (bit & 7))) != 0;
}