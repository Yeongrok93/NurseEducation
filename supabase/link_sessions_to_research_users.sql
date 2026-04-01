-- sessions.user_id를 research_users에 FK 연결
-- 기존에 Supabase Auth UUID가 들어있던 행은 NULL로 초기화

-- 1. user_id 타입을 text -> uuid로 변경
ALTER TABLE public.sessions
  ALTER COLUMN user_id TYPE uuid USING user_id::uuid;

-- 2. research_users에 없는 기존 user_id를 NULL로 정리
UPDATE public.sessions
  SET user_id = NULL
  WHERE user_id IS NOT NULL
    AND user_id NOT IN (SELECT id FROM public.research_users);

-- 3. FK 연결
ALTER TABLE public.sessions
  ADD CONSTRAINT fk_sessions_research_user
  FOREIGN KEY (user_id) REFERENCES public.research_users(id)
  ON DELETE SET NULL;

-- 4. 유저별 조회 인덱스
CREATE INDEX IF NOT EXISTS idx_sessions_user_id
  ON public.sessions (user_id);
