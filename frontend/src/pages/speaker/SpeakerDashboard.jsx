import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import LoadingSpinner from '../../components/LoadingSpinner';
import {
  Plus,
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  Calendar,
  MessageSquare,
  Download,
  Eye,
  Edit,
  Upload,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';

const SpeakerDashboard = () => {
  const { user, apiCall } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch sessions
      const sessionsResponse = await apiCall('/sessions');
      if (sessionsResponse.ok) {
        const sessionsData = await sessionsResponse.json();
        setSessions(sessionsData.sessions || []);
      }

      // Fetch questions
      const questionsResponse = await apiCall('/sessions/questions');
      if (questionsResponse.ok) {
        const questionsData = await questionsResponse.json();
        setQuestions(questionsData.questions || []);
      }

      // Fetch broadcast messages
      const messagesResponse = await apiCall('/messages');
      if (messagesResponse.ok) {
        const messagesData = await messagesResponse.json();
        setMessages(messagesData.messages || []);
      }

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'scheduled':
        return <Calendar className="h-4 w-4 text-blue-500" />;
      case 'submitted':
      case 'under_review':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      draft: 'secondary',
      submitted: 'default',
      under_review: 'default',
      approved: 'default',
      rejected: 'destructive',
      scheduled: 'default',
    };

    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      submitted: 'bg-yellow-100 text-yellow-800',
      under_review: 'bg-blue-100 text-blue-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      scheduled: 'bg-purple-100 text-purple-800',
    };

    return (
      <Badge variant={variants[status]} className={colors[status]}>
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-AU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (loading) {
    return <LoadingSpinner text="Loading your dashboard..." />;
  }

  const draftSessions = sessions.filter(s => s.status === 'draft');
  const submittedSessions = sessions.filter(s => ['submitted', 'under_review', 'approved', 'rejected', 'scheduled'].includes(s.status));
  const openQuestions = questions.filter(q => q.status === 'open');
  const recentMessages = messages.slice(0, 3);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Welcome back, {user?.first_name}!</h1>
          <p className="text-muted-foreground mt-1">
            Manage your session submissions for Cybercon Melbourne 2025
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Button asChild>
            <Link to="/speaker/sessions/new">
              <Plus className="mr-2 h-4 w-4" />
              Submit New Session
            </Link>
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <FileText className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-muted-foreground">Total Sessions</p>
                <p className="text-2xl font-bold">{sessions.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Clock className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-muted-foreground">Under Review</p>
                <p className="text-2xl font-bold">
                  {sessions.filter(s => ['submitted', 'under_review'].includes(s.status)).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-muted-foreground">Approved</p>
                <p className="text-2xl font-bold">
                  {sessions.filter(s => ['approved', 'scheduled'].includes(s.status)).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <MessageSquare className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-muted-foreground">Open Questions</p>
                <p className="text-2xl font-bold">{openQuestions.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="sessions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="sessions">My Sessions</TabsTrigger>
          <TabsTrigger value="questions">Questions & Answers</TabsTrigger>
          <TabsTrigger value="messages">Messages</TabsTrigger>
        </TabsList>

        {/* Sessions Tab */}
        <TabsContent value="sessions" className="space-y-4">
          {/* Draft Sessions */}
          {draftSessions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Edit className="mr-2 h-5 w-5" />
                  Draft Sessions
                </CardTitle>
                <CardDescription>
                  Complete and submit your draft sessions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {draftSessions.map((session) => (
                    <div key={session.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex-1">
                        <h4 className="font-medium">{session.title || 'Untitled Session'}</h4>
                        <p className="text-sm text-muted-foreground">
                          Created {formatDate(session.created_at)}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getStatusBadge(session.status)}
                        <Button asChild size="sm" variant="outline">
                          <Link to={`/speaker/sessions/${session.id}/edit`}>
                            <Edit className="mr-1 h-3 w-3" />
                            Edit
                          </Link>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Submitted Sessions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Upload className="mr-2 h-5 w-5" />
                Submitted Sessions
              </CardTitle>
              <CardDescription>
                Track the status of your submitted sessions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {submittedSessions.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No submitted sessions</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Get started by submitting your first session.
                  </p>
                  <div className="mt-6">
                    <Button asChild>
                      <Link to="/speaker/sessions/new">
                        <Plus className="mr-2 h-4 w-4" />
                        Submit New Session
                      </Link>
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {submittedSessions.map((session) => (
                    <div key={session.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            {getStatusIcon(session.status)}
                            <h4 className="font-medium">{session.title}</h4>
                            {getStatusBadge(session.status)}
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">
                            {session.session_type?.name} • Submitted {formatDate(session.submitted_at)}
                          </p>
                          {session.description && (
                            <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                              {session.description}
                            </p>
                          )}
                          {session.current_file && (
                            <div className="flex items-center mt-2 text-sm text-muted-foreground">
                              <FileText className="mr-1 h-3 w-3" />
                              {session.current_file.original_filename}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-2 ml-4">
                          <Button asChild size="sm" variant="outline">
                            <Link to={`/speaker/sessions/${session.id}`}>
                              <Eye className="mr-1 h-3 w-3" />
                              View
                            </Link>
                          </Button>
                          {['draft', 'rejected'].includes(session.status) && (
                            <Button asChild size="sm" variant="outline">
                              <Link to={`/speaker/sessions/${session.id}/edit`}>
                                <Edit className="mr-1 h-3 w-3" />
                                Edit
                              </Link>
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Questions Tab */}
        <TabsContent value="questions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <MessageSquare className="mr-2 h-5 w-5" />
                Questions & Answers
              </CardTitle>
              <CardDescription>
                Ask questions about your sessions and view responses
              </CardDescription>
            </CardHeader>
            <CardContent>
              {questions.length === 0 ? (
                <div className="text-center py-8">
                  <HelpCircle className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No questions yet</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Questions you ask about your sessions will appear here.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {questions.map((question) => (
                    <div key={question.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <MessageSquare className="h-4 w-4 text-blue-500" />
                            <span className="font-medium">Question about: {question.session?.title}</span>
                            {question.is_urgent && (
                              <Badge variant="destructive" className="text-xs">Urgent</Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mt-2">{question.question_text}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Asked {formatDate(question.created_at)}
                          </p>
                          
                          {question.responses && question.responses.length > 0 && (
                            <div className="mt-3 pl-4 border-l-2 border-green-200">
                              {question.responses.map((response) => (
                                <div key={response.id} className="mb-2">
                                  <p className="text-sm text-gray-700">{response.response_text}</p>
                                  <p className="text-xs text-muted-foreground">
                                    Responded by {response.responder?.first_name} {response.responder?.last_name} on {formatDate(response.created_at)}
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                        <Badge variant={question.status === 'answered' ? 'default' : 'secondary'}>
                          {question.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Messages Tab */}
        <TabsContent value="messages" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Bell className="mr-2 h-5 w-5" />
                Broadcast Messages
              </CardTitle>
              <CardDescription>
                Important announcements and updates from the organizers
              </CardDescription>
            </CardHeader>
            <CardContent>
              {recentMessages.length === 0 ? (
                <div className="text-center py-8">
                  <Bell className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No messages</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Announcements and updates will appear here.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {recentMessages.map((message) => (
                    <div key={message.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium">{message.subject}</h4>
                          <p className="text-sm text-gray-600 mt-1">{message.message}</p>
                          <p className="text-xs text-muted-foreground mt-2">
                            {formatDate(message.sent_at)}
                          </p>
                        </div>
                        {message.message_type === 'urgent' && (
                          <Badge variant="destructive">Urgent</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks and helpful resources
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button asChild variant="outline" className="h-auto p-4">
              <Link to="/speaker/sessions/new" className="flex flex-col items-center space-y-2">
                <Plus className="h-6 w-6" />
                <span>Submit New Session</span>
              </Link>
            </Button>
            
            <Button asChild variant="outline" className="h-auto p-4">
              <Link to="/speaker/faq" className="flex flex-col items-center space-y-2">
                <HelpCircle className="h-6 w-6" />
                <span>View FAQ</span>
              </Link>
            </Button>
            
            <Button variant="outline" className="h-auto p-4" onClick={() => window.location.href = 'mailto:support@cybercon2025.com'}>
              <div className="flex flex-col items-center space-y-2">
                <MessageSquare className="h-6 w-6" />
                <span>Contact Support</span>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SpeakerDashboard;

