struct S {
  char pad0[0x58];
  unsigned char flags;
  char pad1[0x5d - 0x59];
  unsigned char arr[4];
};

extern "C" void func_605fb648(S* s, unsigned int idx, unsigned char val) {
  if (idx > 3)
    return;
  s->flags |= 0x18;
  s->arr[idx] = val;
}