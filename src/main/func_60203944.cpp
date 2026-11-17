extern "C" {
void func_601ff308(void *);
unsigned short func_60203944(void *a, char *b) {
    func_601ff308(a);
    unsigned short v = *(unsigned short *)((char *)a + 0x98);
    *(unsigned short *)(b + 0x2b04) = v;
    return v;
}
}