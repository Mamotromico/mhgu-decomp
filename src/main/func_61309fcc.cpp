extern "C" void func_61309fcc(char *r0, unsigned char r1) {
    unsigned int v = *(unsigned int *)(r0 + 0x8f8);
    if (v == 1) {
        goto store;
    }
    if (v != 0) {
        return;
    }
    *(unsigned int *)(r0 + 0x8f8) = 1;
store:
    *(unsigned char *)(r0 + 0x8fc) = r1;
}