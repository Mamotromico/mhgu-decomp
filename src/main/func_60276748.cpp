struct S {
  unsigned char pad[0x1C];
  int data[1];
};

extern "C" int func_60276748(S *s, int idx) {
  return s->data[idx];
}