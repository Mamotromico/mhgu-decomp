struct dest_613949bc {
    unsigned char pad[8];
    unsigned long long value;
    unsigned char flag;
};

struct src_613949bc {
    unsigned long long value;
};

extern "C" void func_613949bc(dest_613949bc *dst, const src_613949bc *src) {
    dst->value = src->value;
    dst->flag = 1;
}