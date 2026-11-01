extern "C" void func_6095ff14(char* r0, const char* r1) {
    struct In { unsigned int a, b, c; };
    const In* in = reinterpret_cast<const In*>(r1);
    *reinterpret_cast<unsigned int*>(r0 + 0xa0) = in->a;
    *reinterpret_cast<unsigned int*>(r0 + 0xa4) = in->b;
    *reinterpret_cast<unsigned int*>(r0 + 0xa8) = in->c;
    *reinterpret_cast<unsigned int*>(r0 + 0xac) = 0;
}