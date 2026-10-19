struct func_60526554_dst {
    unsigned char pad[0x410];
    unsigned long long value;
};

struct func_60526554_src {
    unsigned long long value;
};

extern "C" void func_60526554(func_60526554_dst *dst, const func_60526554_src *src) {
    dst->value = src->value;
}