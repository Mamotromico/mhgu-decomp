struct S {
    char pad[0x12c];
    unsigned short data[0x100][6][2];
};

extern "C" unsigned short func_601ac4bc(S *s, int a, int b, int c) {
    return s->data[a][b][c];
}