extern "C" void _ZN2nn2os11SleepThreadENS_8TimeSpanE(long long);

extern "C" void func_607bdf2c(unsigned a, unsigned b) {
    unsigned long long p = (unsigned long long)b * 0xf4240ULL;
    unsigned lo = (unsigned)p;
    unsigned hi = (unsigned)(p >> 32);
    (void)lo;
    (void)hi;
    _ZN2nn2os11SleepThreadENS_8TimeSpanE((long long)p);
}