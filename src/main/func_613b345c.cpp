struct src_struct {
    unsigned long long value;
};

struct dst_struct {
    unsigned char pad[0x10];
    unsigned long long value;
};

extern "C" void func_613b345c(dst_struct *dst, const src_struct *src) {
    dst->value = src->value;
}