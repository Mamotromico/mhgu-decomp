struct S_600e0d90 {
    char pad00[0x14];
    char value;
    char pad01[0x17];
};

extern "C" char* func_600e0d90(S_600e0d90* base, int index) {
    return &base[index].value;
}