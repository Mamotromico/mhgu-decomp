extern "C" unsigned int func_60b09e28(unsigned int x) {
    unsigned int i = ~0u;
    do {
        ++i;
    } while ((1u << i) <= x);
    return i;
}