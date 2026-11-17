extern "C" {
void func_607bd990(void *, void *, unsigned);
}
struct S { char pad[0x68]; };
extern "C" void func_601cab90(char *base, unsigned idx, void *src) {
    if (idx > 0x47)
        return;
    func_607bd990(base + idx * sizeof(S), src, sizeof(S));
}