extern "C" void func_608879ac(void *p);

extern "C" void func_610b20d8(void *p) {
    func_608879ac(p);
    *(unsigned *)((char *)p + 0x10) = (*(unsigned *)((char *)p + 0x10) & ~0x2cu) | 0xc;
}