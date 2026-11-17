extern "C" void func_600fd2bc(char *a, unsigned **b) {
    unsigned *p = *b;
    unsigned (*fn)(unsigned *) = (unsigned (*)(unsigned *))*(void **)((char *)p + 0xc);
    unsigned r = fn((unsigned *)b);
    *(unsigned *)(a + 4) = r;
}