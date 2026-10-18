struct __attribute__((aligned(8))) __s64 {
    unsigned long long v;
};

extern "C" void func_61227c10(__s64 *dst, const __s64 *src) {
    *dst = *src;
}