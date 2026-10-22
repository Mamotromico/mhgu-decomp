extern "C" unsigned int func_603021f4(unsigned int x, unsigned int n) {
    unsigned int t = x + (x << 16);
    return (unsigned short)((int)t >> (n & 15));
}